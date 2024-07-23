import { View, Text } from 'react-native'
import React from 'react'
import CustomButton from '../../components/CustomButton'
import { SafeAreaView } from 'react-native-safe-area-context'
import { router } from 'expo-router'
const userTypeSelection = () => {
  return (
    <SafeAreaView className= "h-full justify-center items-center bg-primary ">
        <Text className="text-3xl text-white font-bold text-center justify-center">Select Account Type</Text>
        <CustomButton
        title = "User"
        handlePress ={() => router.push('/sign-up')} 
        containerStyles="w-[200px] mt-7"
        textStyles="text-xl"
        />

    <CustomButton
        title = "Masjid"
        handlePress ={() => router.push('/Mosque-sign-up')} 
        containerStyles="w-[200px] mt-7"
        textStyles="text-xl"
        />
    </SafeAreaView>
  )
}

export default userTypeSelection