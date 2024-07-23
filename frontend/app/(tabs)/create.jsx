import { View, Text, TextInput} from 'react-native'
import React, { useState } from 'react'
import { SafeAreaView } from 'react-native-safe-area-context';


const Create = () => {
  const [value, setValue] = useState(''); // Initialize state for text input

  return (
    <SafeAreaView className="bg-primary h-full justify-center items-center">
      <TextInput
        editable
        multiline
        numberOfLines={4}
        maxLength={40}
        onChangeText={text => setValue(text)} // Update state on text change
        value={value} // Bind state to value prop
        className="p-2 border border-gray-300 rounded bg-white text-black"
      />
    </SafeAreaView>
  );
};

export default Create;