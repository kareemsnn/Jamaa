// import { StatusBar } from 'expo-status-bar';
// import { ScrollView, Text, View, Image } from 'react-native';
// import {Link, Redirect, router} from 'expo-router';
// import {SafeAreaView} from 'react-native-safe-area-context';
// import { images } from '../constants';
// import CustomButton from '../components/CustomButton';

// export default function landingPage() {
//   return (
//     <SafeAreaView className = 'bg-primary h-full'>
//       <ScrollView contentContainerStyle = {{height: '100%'}}>
//         <View className =" w-full  items-center min-h-[85vh] px-4">
//           <Image
//             source = {images.logo}
//             className = "w-[130px] h-[84px]"
//             resizeMode = "contain"
//           />
//           <Image 
//           source={require('../assets/images/orangeMosque.png')}
//           className="max-w-[230px] w-full h-[300px]"
//           resizeMode='contain'
//           />
//           <View className = "relative mt-5">
//             <Text className = "text-3xl text-white font-bold text-center"> Welcome to
//             <Text className = "text-secondary-200"> Masjidy{"\n"}</Text>
//             </Text>
//           </View>

//           <Text className="text-sm font-pregular text-white mt-7 text-center mb-5">Where you can find all the masjids around you 
//           and find nearby events</Text>
          
//           <CustomButton
//           title = "Sign Up/Sign In"
//           handlePress ={() => router.push('/sign-in')} 
//           containerStyles="w-full mt-7"/>

//           <Link href='/home' className="text-white pt-5">Skip Sign-In</Link>

//         </View>
//       </ScrollView>
//       <StatusBar backgroundColor='#161622' style='light'/>
//     </SafeAreaView>  
//     );
// }
