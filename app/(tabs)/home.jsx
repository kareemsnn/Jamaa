import { View, Text, FlatList, Image, RefreshControl } from 'react-native'
import React, { useState } from 'react'
import {SafeAreaView} from 'react-native-safe-area-context'
import {images} from '../../constants'
import SearchInput from '../../components/SearchInput'
import Trending from '../../components/Trending'
import EmptyState from '../../components/EmptyState'

const Home = () => {
  const [refreshing, setRefreshing] = useState(false)

  const onRefresh = async () => {
    setRefreshing(true);
    setRefreshing(false);
  }

  return (
    <SafeAreaView className="bg-primary h-full">
      <FlatList 
      data = {[{id : 1}, {id : 2}, {id : 3}]}
      keyExtractor = {(item =>item.$id)}
      renderItem={({item}) => (
        <Text className="text-3xl text-white">{item.id}</Text>
      )}
      ListHeaderComponent={()=>(
        <View className="flex mt-6 px-4 space-y-6">
          <View className="flex-row justify-between items-start">
            <View>
              <Text className="font-pmedium text-sm text-gray-100">
                Welcome Back
              </Text>
              <Text className="text-2xl font-psemibold text-white">
                Kareem
              </Text>
            </View>
            
            <View className="mt-1.5">
              <Image 
                source={images.logoSmall}
                className="w-9 h-10"
                resizemode='contain'
                />
            </View>
          </View>

          <SearchInput/>

          <View className="w-full flex-1 pt-5 pb-8">
            <Text className="text-lg font-pregular text-gray-100 mb-3">
              Latest Videos
            </Text>

            <Trending posts={[{id : 1}, {id : 2}, {id : 3}] ?? []} />

          </View>
        </View>
      )}
      ListEmptyComponent={() => (
        <EmptyState
        title="No Videos Found"
        subtitle="Be the first to upload a post!"
        />
      )}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh}/>}
      />
    </SafeAreaView>
  )
}

export default Home