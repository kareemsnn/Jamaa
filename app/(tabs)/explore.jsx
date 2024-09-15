import React, { useState, useEffect, useContext } from 'react';
import { View, Text, FlatList, TouchableOpacity, Image, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Context } from '../../components/globalContext';
import { icons } from '../../constants';
import SearchInput from '../../components/SearchInput';

const Explore = () => {
  const router = useRouter();
  const { getNearbyMosques } = useContext(Context);
  const [nearbyMosques, setNearbyMosques] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchNearbyMosques();
  }, []);

  const fetchNearbyMosques = async () => {
    setIsLoading(true);
    try {
      const mosques = await getNearbyMosques();
      setNearbyMosques(mosques);
    } catch (error) {
      console.error('Error fetching nearby mosques:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMosquePress = (mosque) => {
    if (mosque && mosque.id) {
      router.push(`/mosque/${mosque.id}`);
    } else {
      console.error('Invalid mosque object:', mosque);
      Alert.alert('Error', 'Unable to view mosque profile.');
    }
  }

  if (isLoading) {
    return (
      <View className="flex-1 justify-center items-center bg-primary">
        <Text className="font-psemibold text-white text-2xl">Loading...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView className="bg-primary h-full">
      <View className="px-4 mt-8">
        <Text className="text-white text-2xl font-psemibold mb-4">
          Nearby Mosques
        </Text>
        <SearchInput />
      </View>
      <FlatList
        data={nearbyMosques}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({item}) => (
          <TouchableOpacity 
            onPress={() => handleMosquePress(item)}
            className="bg-black-100 p-4 m-2 rounded-lg"
          >
            <Text className="text-white text-lg font-psemibold">Mosque ID: {item.id}</Text>
            <Text className="text-gray-300 mt-1">Distance: {item.distance_miles} miles</Text>
          </TouchableOpacity>
        )}
        ListEmptyComponent={() => (
          <View className="flex-1 justify-center items-center mt-10">
            <Text className="text-white text-lg">No nearby mosques found</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
};

export default Explore;