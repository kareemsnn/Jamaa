import { useRouter } from "expo-router";
import {jwtDecode} from "jwt-decode";
import api from "../api.js";
import {ACCESS_TOKEN, REFRESH_TOKEN} from "../tokens.js";
import {useState, useEffect} from "react";
import AsyncStorage from "react-native";

function ProtectedRoute({children}) {
    const [isAuthorized,setIsAuthorized] = useState(null)
    const router = useRouter();

    useEffect(() => {
        auth().catch(() => setIsAuthorized(false))
    }, [])

    const refreshToken = async () => {
        const refresh = AsyncStorage.getItem(REFRESH_TOKEN);
        try{
            const res = await api.post("/api/token/refresh/", {
                refresh: refreshToken,
            });
            if (res.status === 200) {
                localStorage.setItem(ACCESS_TOKEN, res.data.access);
                setIsAuthorized(true)
            } else {
                setIsAuthorized(false)
            }

        } catch (error) {
            console.log(error)
            setIsAuthorized(false)
        }
    };

    const auth = async () => {
        const token = AsyncStorage.getItem(ACCESS_TOKEN);
        if (!token) {
            setIsAuthorized(false);
            return;
        }
        const decoded = jwtDecode(token);
        const tokenExpiration = decoded.exp
        const now = Date.now() / 1000

        if (tokenExpiration < now) {
            await refreshToken()
        }
        else{
            setIsAuthorized(true)
        }
    };

    if(isAuthorized===null){
        return <div>Loading...</div>
    }

    if (!isAuthorized) {
        router.push('/sign-in'); 
        return null; 
    }

    return children;
}

export default ProtectedRoute;