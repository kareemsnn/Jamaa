import { View, Text, ScrollView, Image } from 'react-native';
import React, {useState} from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {images} from '../../constants';
import FormField from '../../components/FormField';
import CustomButton from '../../components/CustomButton';
import {Link} from 'expo-router';
import { loginUser } from '../../apiRequests';

const SignIn = () => {
const [form, setForm] = useState ({
  email: '',
  password: ''
})

const [isSubmitting, setisSubmitting] = useState(false)

const submit = async () => {
  setIsSubmitting(true);
  try {
    const userData = {
      username: form.email, // Assuming you're using email as the username
      password: form.password,
    };
    const response = await loginUser(userData);
    console.log('User logged in successfully:', response);
    // Optionally, save the token and navigate to another screen
    // e.g., save the token in async storage and navigate to the home screen
  } catch (error) {
    console.error('Error logging in:', error);
    // Optionally, show an error message to the user
  } finally {
    setIsSubmitting(false);
  }
};

  return (
    <SafeAreaView className ="bg-primary h-full">
     <ScrollView>
      <View className="w-full justify-center min-h-[75vh] px-4 my-6">
        <Image source = {images.logo}
        resizeMode='contain' className="w-[115px] h-[35px]"/>
        <Text className = "text-2xl text-white mt-10 font-psemibold">Log in to the Masjid App</Text>
        
        <FormField 
        title= "Email"
        value={form.email}
        handleChangeText ={(e) => setForm ({ ...form, email: e})}
        otherStyles="mt-7"
        keyboardType="email-address"
        />

        <FormField 
        title= "Password"
        value={form.password}
        handleChangeText ={(e) => setForm ({ ...form, password: e})}
        otherStyles="mt-7"
        />

        <CustomButton
        title ="Sign-in"
        handlePress={submit}
        containerStyles="mt-7"
        isLoading = {isSubmitting}
        />
        <View className="justify-center pt-5 flex-row gap-2">
          <Text className ="text-lg text-gray-100 font-pregular">
            Don't have an account?
          </Text>
          <Link href ="/sign-up" className ="text-lg font-psemibold text-secondary">Sign Up</Link>
          
        </View>
      </View>
     </ScrollView>
    </SafeAreaView>
  )
}

export default SignIn