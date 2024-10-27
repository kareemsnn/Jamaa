from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser, Mosque, Post, Follow
from .serializers import CustomUserSerializer, MosqueSerializer, PostEventForm, PostSerializer,FollowSerializer
from django.contrib.auth.models import Permission
from .updatelocation import get_location
from .utils import get_grid
from django.core.cache import cache
from .models import Events
import logging
from django.http import HttpResponse
import time
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .utils import haversine,get_grid,GRID_SIZE
from django.db.models import Q
from django.shortcuts import get_object_or_404
logger = logging.getLogger(__name__)
import boto3
import json
import os
from dotenv import load_dotenv
import openai
import pytesseract
from PIL import Image
import base64
import io
from openpyxl import Workbook
import pandas as pd
from datetime import time

from openai import OpenAI
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)
pytesseract_path = os.getenv('PYTESSERACT_PATH')
pytesseract.pytesseract.tesseract_cmd = pytesseract_path

def index(request):
    return HttpResponse("Welcome to the Mosque App")


CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

class RegisterUserView(APIView):
    def post(self, request):
        logger.info("Starting user registration")
        start_time = time.time()

        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            role = validated_data['role']
            logger.info(f"Validation successful for role: {role}")

            if role == 'mosque':
                address = request.data.get('address')
                lat, lon = get_location(address)
                logger.info(f"Retrieved location for address {address}: lat={lat}, lon={lon}")

                if lat is None or lon is None:
                    return Response({'error': 'Invalid address'}, status=status.HTTP_400_BAD_REQUEST)
                
                grid_lat, grid_lon = get_grid(lat, lon)

                user_start_time = time.time()
                user = CustomUser.objects.create(
                    username=validated_data['username'],
                    email=validated_data['email'],
                    role=role,
                    latitude=lat,
                    longitude=lon,
                )
                user.set_password(validated_data['password'])
                user.save()
                user_creation_time = time.time() - user_start_time
                logger.info(f"Created user: {user} in {user_creation_time:.2f} seconds")

                permissions = [
                    Permission.objects.get(codename='can_change_prayer_times'),
                    Permission.objects.get(codename='can_post_announcements'),
                    Permission.objects.get(codename='can_put_up_events'),
                    Permission.objects.get(codename='can_post_media'),
                ]
                user.user_permissions.set(permissions)
                logger.info(f"Assigned permissions to user: {permissions}")

                mosque_start_time = time.time()
                mosque = Mosque.objects.create(
                    user=user,
                    email=user.email,
                    mosquename=user.username,
                    address=address,
                    lat=lat,
                    lon=lon,
                    grid_cell_lat=grid_lat,
                    grid_cell_lon=grid_lon,
                )
                mosque_creation_time = time.time() - mosque_start_time
                logger.info(f"Created mosque: {mosque} in {mosque_creation_time:.2f} seconds")

            elif role == 'user':
                latitude = request.data.get('latitude')
                longitude = request.data.get('longitude')

                grid_lat, grid_lon = get_grid(latitude, longitude)

                user_start_time = time.time()
                user = CustomUser.objects.create(
                    username=validated_data['username'],
                    email=validated_data['email'],
                    role=role,
                    latitude=latitude,
                    longitude=longitude,
                    grid_cell_lat=grid_lat,
                    grid_cell_lon=grid_lon,
                )
                user.set_password(validated_data['password'])
                user.save()
                user_creation_time = time.time() - user_start_time
                logger.info(f"Created user: {user} in {user_creation_time:.2f} seconds")

            refresh = RefreshToken.for_user(user)

            total_time = time.time() - start_time
            logger.info(f"Total registration time: {total_time:.2f} seconds")

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        logger.error(f"User registration failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UpdateMosqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, mosque_id):
        try:
            return Mosque.objects.get(mosque_id=mosque_id)
        except Mosque.DoesNotExist:
            logger.error(f"Mosque with id {mosque_id} not found")
            return None

    def put(self, request, mosque_id):
        logger.info(f"Starting update for mosque id: {mosque_id}")
        mosque = self.get_object(mosque_id)
        if mosque is None:
            return Response({'error': 'Mosque not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user != mosque.user:
            logger.error(f"Permission denied for user {request.user} to update mosque {mosque_id}")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = MosqueSerializer(mosque, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Updated mosque: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.error(f"Update mosque failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FollowMosqueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, mosque_id):
        logger.info(f"User {request.user} attempting to follow mosque id: {mosque_id}")
        try:
            mosque = Mosque.objects.get(mosque_id=mosque_id)
        except Mosque.DoesNotExist:
            logger.error(f"Mosque with id {mosque_id} not found")
            return Response({'error': 'Mosque not found'}, status=status.HTTP_404_NOT_FOUND)

        Follow.objects.get_or_create(user=request.user, mosque=mosque)
        logger.info(f"User {request.user} followed mosque {mosque_id}")
        return Response({'status': 'Mosque followed'}, status=status.HTTP_200_OK)

    def delete(self, request, mosque_id):
        logger.info(f"User {request.user} attempting to unfollow mosque id: {mosque_id}")
        try:
            mosque = Mosque.objects.get(mosque_id=mosque_id)
        except Mosque.DoesNotExist:
            logger.error(f"Mosque with id {mosque_id} not found")
            return Response({'error': 'Mosque not found'}, status=status.HTTP_404_NOT_FOUND)

        Follow.objects.filter(user=request.user, mosque=mosque).delete()
        logger.info(f"User {request.user} unfollowed mosque {mosque_id}")
        return Response({'status': 'Mosque unfollowed'}, status=status.HTTP_200_OK)


class PostAnnouncementView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"User {request.user} attempting to post announcement")
        if not request.user.has_perm('myapp.can_post_announcements'):
            logger.error(f"Permission denied for user {request.user} to post announcement")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Announcement posted: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Post announcement failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostMediaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"User {request.user} attempting to post media")
        if not request.user.has_perm('myapp.can_post_media'):
            logger.error(f"Permission denied for user {request.user} to post media")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        file_name = request.data.get('file_name')
        file_type = request.data.get('file_type')

        s3_client = boto3.client('s3', region_name=settings.AWS_S3_REGION_NAME,
                                 aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
       
        try:
            # Generate pre-signed URL for direct upload to S3
            presigned_url = s3_client.generate_presigned_url('put_object',
                                                             Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                                     'Key': f"media/{file_name}",
                                                                     'ContentType': file_type},
                                                             ExpiresIn=3600)  # URL expires in 1 hour
            return Response({'url': presigned_url, 'file_name': file_name}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error generating pre-signed URL: {e}")
            return Response({'error': 'Failed to generate upload URL'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PostEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"User {request.user} attempting to post event")
        if not request.user.has_perm('myapp.can_put_up_events'):
            logger.error(f"Permission denied for user {request.user} to post event")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PostEventForm(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Event posted: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Post event failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LikePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        logger.info(f"User {request.user} attempting to like post id: {post_id}")
        try:
            post = Post.objects.get(post_id=post_id)
        except Post.DoesNotExist:
            logger.error(f"Post with id {post_id} not found")
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        
        post.likes.add(request.user)
        logger.info(f"Post {post_id} liked by user {request.user}")
        return Response({'status': 'Post liked'}, status=status.HTTP_200_OK)

    def delete(self, request, post_id):
        logger.info(f"User {request.user} attempting to unlike post id: {post_id}")
        try:
            post = Post.objects.get(post_id=post_id)
        except Post.DoesNotExist:
            logger.error(f"Post with id {post_id} not found")
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        
        post.likes.remove(request.user)
        logger.info(f"Post {post_id} unliked by user {request.user}")
        return Response({'status': 'Post unliked'}, status=status.HTTP_200_OK)


# views.py
import time
import logging
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Mosque
from .serializers import MosqueSerializer
from .utils import get_grid, haversine  # Importing functions from utils.py

logger = logging.getLogger(__name__)




AVERAGE_DRIVING_SPEED_MPH = 45  
DRIVING_TIME_MINUTES = 30  
DRIVING_DISTANCE_MILES = (AVERAGE_DRIVING_SPEED_MPH / 60) * DRIVING_TIME_MINUTES  
KM_TO_MILES = 0.621371  

class NearbyMosquesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lat = float(request.query_params.get('lat'))
        lon = float(request.query_params.get('lon'))
        distance_miles = DRIVING_DISTANCE_MILES  # max mosque distance is within a 30 minute drive or 20 miles subject to user preference
                                                 # can be increased or decreased in settings but for now its hard coded 
                                                 #later can be changed into a variable 

        logger.info(f"User {request.user} requesting nearby mosques for lat: {lat}, lon: {lon}, distance: {distance_miles} miles")

        # Convert driving distance in miles to kilometers 
        distance_km = distance_miles / KM_TO_MILES

        grid_lat, grid_lon = get_grid(lat, lon)
        radius_in_degrees = distance_km / 111  # Convert distance to degrees
        grid_radius = int(radius_in_degrees / GRID_SIZE) + 1

        start_time = time.time()

        # Query to get nearby grids
        nearby_grids_query = Q()
        for dx in range(-grid_radius, grid_radius + 1):
            for dy in range(-grid_radius, grid_radius + 1):
                nearby_grids_query |= Q(grid_cell_lat=grid_lat + dx, grid_cell_lon=grid_lon + dy)

        # Fetching mosques in the nearby grids
        nearby_mosques = Mosque.objects.filter(nearby_grids_query).only('mosque_id', 'lat', 'lon')

        # Filter mosques by actual distance and sort by closest distance
        mosques = []
        for mosque in nearby_mosques:
            distance_to_mosque_km = haversine(lat, lon, mosque.lat, mosque.lon)
            distance_to_mosque_miles = distance_to_mosque_km * KM_TO_MILES
            if distance_to_mosque_miles <= distance_miles:
                mosques.append({
                    'mosque_id': mosque.mosque_id,
                    "mosquename":mosque.mosquename,
                    'distance_miles': f"{distance_to_mosque_miles:.2f}"
                })

        # Sort mosques by distance_miles
        mosques.sort(key=lambda x: x['distance_miles'])

        total_time = time.time() - start_time
        logger.info(f"Nearby mosques fetched in {total_time:.2f} seconds")

        return Response(mosques, status=status.HTTP_200_OK)


class MosqueVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"User {request.user} attempting to verify mosque")
        # verification logic here 
        # currently working on ways to verify mosques
        return Response({'status': 'Mosque verification logic not implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class GetUsersView(ListAPIView):
    """
    View to list all users or filter users by mosquename.
    """
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = CustomUser.objects.all()
        mosquename = self.request.query_params.get('mosquename', None)
        if mosquename is not None:
            queryset = queryset.filter(mosque__mosquename=mosquename)
        return queryset

class GetUserDetailView(RetrieveAPIView):
    """
    View to retrieve a user by ID.
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]


class GetMosqueDetailView(RetrieveAPIView):
    """
    View to retrieve a mosque by ID or name.
    """
    queryset = Mosque.objects.all()
    serializer_class = MosqueSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Get the value from URL parameters
        lookup_value = self.kwargs.get('lookup_value')

        # Try to get the mosque by ID or by name
        if lookup_value.isdigit():
            # If it's a digit, assume it's an ID
            return get_object_or_404(Mosque, pk=lookup_value)
        else:
            # Otherwise, assume it's a name
            return get_object_or_404(Mosque, name=lookup_value)

class GetPostsView(ListAPIView):
    """
    View to list all posts or filter posts by mosquename.
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Post.objects.all()
        mosquename = self.request.query_params.get('mosquename', None)
        if mosquename is not None:
            queryset = queryset.filter(mosque__mosquename=mosquename)
        return queryset

class GetPostDetailView(RetrieveAPIView):
    """
    View to retrieve a post by ID.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]


class UserProfileView(APIView):
    """
    View to retrieve a mosque's profile along with their posts and events.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mosque_id = request.query_params.get('mosque_id')
        mosquename = request.query_params.get('mosquename')
        
        try:
            if mosque_id:
                mosque = get_object_or_404(Mosque, mosque_id=mosque_id)
            elif mosquename:
                mosque = get_object_or_404(Mosque, mosquename=mosquename)
            else:
                user = request.user
                if user.role != 'mosque':
                    return Response({'error': 'Profile not available'}, status=status.HTTP_403_FORBIDDEN)
                mosque = user.mosque
        except Mosque.DoesNotExist:
            return Response({'error': 'Mosque not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = MosqueSerializer(mosque)
        return Response(serializer.data, status=status.HTTP_200_OK)

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate, get_user_model
from .serializers import CustomUserSerializer
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if username is None or password is None:
            return Response({'error': 'Please provide both username and password.'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Authenticating user with username: {username}")

        user = authenticate(request, username=username, password=password)
        logger.info(f"Authentication result for {username}: {user}")

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': CustomUserSerializer(user).data
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Authentication failed for user: {username}")
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)



class NearbyEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lat = float(request.query_params.get('lat'))
        lon = float(request.query_params.get('lon'))

        logger.info(f"User {request.user} requesting nearby events for lat: {lat}, lon: {lon}")

        # Call the existing nearby mosques view to get nearby mosques
        nearby_mosques_view = NearbyMosquesView()
        mosques_response = nearby_mosques_view.get(request).data

        # Extract mosque IDs from the response
        mosque_ids = [mosque['id'] for mosque in mosques_response]

        # Fetch events for the nearby mosques
        events = Events.objects.filter(mosque_id__in=mosque_ids).order_by('event_date')

        events_list = []
        for event in events:
            events_list.append({
                'mosque_id': event.mosque_id,
                'event_title': event.event_title,
                'event_date': event.event_date,
                'location': event.location,
                'event_description': event.event_description,
                'rsvp': event.rsvp
            })

        logger.info(f"Nearby events fetched successfully")

        return Response(events_list, status=status.HTTP_200_OK)
    


class DeletePostsView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, post_id):
        logger.info(f"User {request.user} attempting to delete post id: {post_id}")
        
        try:
            post = Post.objects.get(post_id=post_id)
        except Post.DoesNotExist:
            logger.error(f"Post with id {post_id} not found")
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # The mosque associated with the post
        mosque = post.mosque

        # The user associated with the mosque
        mosque_user = mosque.user

        # Check if the requesting user is the mosque user or has the appropriate role
        if request.user != mosque_user and request.user.role != 'mosque':
            logger.error(f"User {request.user} does not have permission to delete post {post_id}")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        post.delete()
        logger.info(f"Post {post_id} deleted by user {request.user}")
        return Response({'status': 'Post deleted successfully'}, status=status.HTTP_200_OK)
    


class SavePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # The logged-in user who created the post
        data = request.data

        # Get the mosque by mosque_id or name
        mosque_id = data.get('mosque_id')
        mosque_name = data.get('mosque_name')

        try:
            if mosque_id:
                mosque = Mosque.objects.get(mosque_id=mosque_id)  
            elif mosque_name:
                mosque = Mosque.objects.get(mosquename=mosque_name)
            else:
                return Response({'error': 'Mosque ID or name is required'}, status=status.HTTP_400_BAD_REQUEST)
        except Mosque.DoesNotExist:
            return Response({'error': 'Mosque not found'}, status=status.HTTP_404_NOT_FOUND)

        
        post_data = {
            'title': data.get('title',''),
            'posttype': data.get('posttype', ''),
            'content': data.get('content', ''),
            'media_file': data.get('media_url', ''),
            'media_type': data.get('media_type', ''),
            'mosque': mosque.mosque_id,  
        }

        
        serializer = PostSerializer(data=post_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class EditPostView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, post_id):
        logger.info(f"User {request.user} attempting to edit post id: {post_id}")
        
        try:
            post = Post.objects.get(post_id=post_id)
        except Post.DoesNotExist:
            logger.error(f"Post with id {post_id} not found")
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the requesting user is the mosque user or has the appropriate role
        if request.user != post.mosque.user and request.user.role != 'mosque':
            logger.error(f"User {request.user} does not have permission to edit post {post_id}")
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Post {post_id} edited by user {request.user}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.error(f"Edit post failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  
    
class EditProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        logger.info(f"User {request.user} attempting to edit profile")
        
        try:
            user = request.user
            user.username = request.data.get('username', user.username)
            user.email = request.data.get('email', user.email)
            user.mosquename = request.data.get('mosquename', user.mosquename)
            user.address = request.data.get('address', user.address)
            user.latitude = request.data.get('latitude', user.latitude)
            user.longitude = request.data.get('longitude', user.longitude)
            user.prayer_times = request.data.get('prayer_times', user.prayer_times)
            user.save()
            logger.info(f"Profile updated for user {user}")
            return Response({'status': 'Profile updated successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class EditMosqueView(APIView):
    permission_classes = [IsAuthenticated] 

    def put(self, request):
        logger.info(f"User {request.user} attempting to edit mosque")

        try:
            mosque = request.user.mosque
        except Mosque.DoesNotExist:
            logger.error(f"Mosque for user {request.user} not found")
            return Response({'error': 'Mosque not found'}, status=status.HTTP_404_NOT_FOUND)

        mosque.mosquename = request.data.get('mosquename', mosque.mosquename)
        mosque.email = request.data.get('email', mosque.email)
        mosque.description = request.data.get('description', mosque.description)
        mosque.profile_pic = request.data.get('profile_pic', mosque.profile_pic)
        mosque.prayer_times = request.data.get('prayer_times', mosque.prayer_times)
        mosque.address = request.data.get('address', mosque.address)
        mosque.lat = request.data.get('lat', mosque.lat)
        mosque.lon = request.data.get('lon', mosque.lon)
        mosque.grid_cell_lat = request.data.get('grid_cell_lat', mosque.grid_cell_lat)
        mosque.grid_cell_lon = request.data.get('grid_cell_lon', mosque.grid_cell_lon)

        try:
            mosque.save()
            logger.info(f"Mosque profile updated for user {request.user}")
            return Response({'status': 'Mosque profile updated successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Mosque profile update failed: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    



class DeleteEventView(APIView):
    permission_classes=[IsAuthenticated]

    def delete(self,request,event_id):
        logger.info(f"User {request.user} attempting to delete event id: {event_id}")
    
        try:
            event=Events.object.get(event_id=event_id)
        except Events.DoesNotExist:
            return Response({'error':'Event not found'},status=status.HTTP_404_NOT_FOUND)
        
        # The mosque associated with the event
        mosque=event.mosque

        # The user associated with the mosque
        mosque_user=mosque.user

        # Check if the requesting user is the mosque user or has the appropriate role
        if request.user != mosque_user and request.user.role != 'mosque':
            logger.error(f"User {request.user} does not have permission to delete event {event_id}")
            return Response({'error':'Permission denied'},status=status.HTTP_403_FORBIDDEN)
        
        event.delete()
        logger.info(f"Event {event_id} deleted by user {request.user}")
        return Response({'status':'Event deleted successfully'},status=status.HTTP_200_OK)
    


        




logger = logging.getLogger(__name__)

class PrayerTimeUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"User {request.user} attempting to upload prayer times")

        excel_file = request.FILES.get('file')
        if not excel_file:
            return Response({'error': 'No Excel file uploaded'}, status=400)

        # Step 1: Extract data from the Excel file
        try:
            json_data = self.extract_data_from_excel(excel_file)
            logger.info(f"Extracted Data:\n{json_data}")
        except Exception as e:
            logger.error(f"Failed to extract data from Excel: {e}")
            return Response({'error': 'Failed to extract data from Excel'}, status=500)

        # Step 2: Send data to OpenAI and get the structured result
        try:
            structured_result = self.send_to_openai(json_data)
            logger.info(f"Structured JSON from OpenAI:\n{structured_result}")
        except Exception as e:
            logger.error(f"Failed to process data with OpenAI: {e}")
            return Response({'error': 'Failed to process data with OpenAI'}, status=500)

        # Save the prayer times to the mosque's prayer_times field
        try:
            prayer_times_dict = structured_result
            mosque = request.user.mosque
            mosque.prayer_times = prayer_times_dict
            mosque.save()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            return Response({'error': 'Invalid JSON format from AI'}, status=500)

        logger.info(f"Prayer times uploaded successfully for mosque {mosque}")
        return Response({'status': 'Prayer times uploaded successfully'}, status=200)

    def extract_data_from_excel(self, excel_file):
        df = pd.read_excel(excel_file)
        # Convert the DataFrame to a list of dictionaries
        return df.to_dict(orient='records')

    def send_to_openai(self, data):
        # Convert time objects to strings
        data = self.convert_time_to_string(data)
        
        # Convert the dictionary to a JSON string
        json_data = json.dumps(data)
        
        prompt = (
            "Extract iqama times for each day from the following data and return them in a structured JSON format. "
            "Use the date as the key and include only the iqama times. Ensure the output is valid JSON:\n"
            f"{json_data}"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()

        try:
            start_index = content.find('{')
            end_index = content.rfind('}') + 1
            json_str = content[start_index:end_index]
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            raise ValueError("Invalid JSON format from AI")

    def convert_time_to_string(self, data):
        for entry in data:
            for key, value in entry.items():
                if isinstance(value, time):
                    entry[key] = value.strftime("%H:%M")
        return data



### get events for a specific mosque









