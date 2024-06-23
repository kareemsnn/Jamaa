import { View, Text, ScrollView, Image } from 'react-native';
import React, { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { images } from '../../constants';
import FormField from '../../components/FormField';
import CustomButton from '../../components/CustomButton';
import { Link } from 'expo-router';
import { Picker } from '@react-native-picker/picker';
import { registerUser } from '../../apiRequests';

const SignUp = () => {
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const submit = async () => {
    setIsSubmitting(true);
    try {
      const userData = {
        username: form.username,
        email: form.email,
        password: form.password,
        role:"user"
      };
      const response = await registerUser(userData);
      console.log('User registered successfully:', response);
      // Optionally, redirect to another page or show a success message
    } catch (error) {
      console.error('Error registering user:', error);
      // Optionally, show an error message to the user
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SafeAreaView className="bg-primary h-full">
      <ScrollView>
        <View className="w-full justify-center min-h-[75vh] px-4 my-6">
          <Image source={images.logo} resizeMode='contain' className="w-[115px] h-[35px]" />
          <Text className="text-2xl text-white mt-10 font-psemibold">Sign Up to the Masjid App</Text>

          <FormField
            title="Username"
            value={form.username}
            handleChangeText={(e) => setForm({ ...form, username: e })}
            otherStyles="mt-10"
          />

          <FormField
            title="Email"
            value={form.email}
            handleChangeText={(e) => setForm({ ...form, email: e })}
            otherStyles="mt-7"
            keyboardType="email-address"
          />

          <FormField
            title="Password"
            value={form.password}
            handleChangeText={(e) => setForm({ ...form, password: e })}
            otherStyles="mt-7"
            secureTextEntry={true} // Added secureTextEntry to hide the password
          />

          {/* <Text className="text-lg text-gray-100 mt-7">Account Type</Text>
          <View style={{ backgroundColor: '#333', borderRadius: 4, marginTop: 10 }}>
            <Picker
              selectedValue={form.accountType}
              style={{ height: 50, color: 'white' }}
              onValueChange={(itemValue) => setForm({ ...form, accountType: itemValue })}
            >
              <Picker.Item label="User" value="user" />
              <Picker.Item label="Mosque" value="mosque" />
            </Picker>
          </View> */}

          <CustomButton
            title="Sign Up"
            handlePress={submit}
            containerStyles="mt-7"
            isLoading={isSubmitting}
          />

          <View className="justify-center pt-5 flex-row gap-2">
            <Text className="text-lg text-gray-100 font-pregular">
              Have an account Already?
            </Text>
            <Link href="/sign-in" className="text-lg font-psemibold text-secondary">Sign in</Link>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default SignUp;
