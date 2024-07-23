import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/MosqueApp/';

export const getAllPosts = async () => {
  try {
    const response = await axios.get(`${API_URL}/posts/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching posts:', error);
    throw error;
  }
};

export const getLatestPosts = async () => {
  try {
    const response = await axios.get(`${API_URL}/posts/latest/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching latest posts:', error);
    throw error;
  }
};

export const registerUser = async (userData) => {
    try {
      const response = await axios.post(`${API_URL}/register/`, userData);
      return response.data;
    } catch (error) {
      console.error('Error registering user:', error);
      throw error;
    }
  };

export const loginUser = async (userData) => {
  try {
    const response = await axios.post(`${API_URL}/api-token-auth/`, userData);
    return response.data;
  } catch (error) {
    console.error('Error logging in:', error);
    throw error;
  }
};