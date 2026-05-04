import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import * as SecureStore from "expo-secure-store";

import {
  type AppUser,
  type ImaginaryFriendAvatar,
  getAvatarProfileRequest,
  getCurrentUser,
  loginRequest,
  registerRequest,
  updateAvatarProfileRequest,
  updateFriendPreferencesRequest,
  type UpdateAvatarPayload,
  type UpdateFriendPreferencesPayload,
} from "./api";

const TOKEN_KEY = "mobile_access_token";
const USER_KEY = "mobile_user";
const AVATAR_KEY = "mobile_avatar_profile";

const DEFAULT_AVATAR_PROFILE: ImaginaryFriendAvatar = {
  face_shape: "redondo",
  primary_color: "azul",
  hair_style: "corto",
  hair_color: "castano",
  eye_style: "felices",
  mouth_style: "sonrisa",
  accessory: "estrella",
  background_style: "cielo",
};

type AuthContextValue = {
  user: AppUser | null;
  token: string | null;
  avatarProfile: ImaginaryFriendAvatar;
  isLoading: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signUp: (
    displayName: string,
    username: string,
    password: string
  ) => Promise<void>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
  updateFriendPreferences: (
    payload: UpdateFriendPreferencesPayload
  ) => Promise<void>;
  updateAvatarProfile: (
    payload: UpdateAvatarPayload
  ) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [avatarProfile, setAvatarProfile] = useState<ImaginaryFriendAvatar>(
    DEFAULT_AVATAR_PROFILE
  );
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const restoreSession = async () => {
      try {
        const savedToken = await SecureStore.getItemAsync(TOKEN_KEY);
        const savedUser = await SecureStore.getItemAsync(USER_KEY);
        const savedAvatar = await SecureStore.getItemAsync(AVATAR_KEY);

        if (!savedToken || !savedUser) {
          setIsLoading(false);
          return;
        }

        const parsedUser = JSON.parse(savedUser) as AppUser;
        const parsedAvatar = savedAvatar
          ? (JSON.parse(savedAvatar) as ImaginaryFriendAvatar)
          : DEFAULT_AVATAR_PROFILE;

        setToken(savedToken);
        setUser(parsedUser);
        setAvatarProfile(parsedAvatar);

        const freshUser = await getCurrentUser(savedToken);
        const freshAvatar = await getAvatarProfileRequest(savedToken);

        setUser(freshUser);
        setAvatarProfile(freshAvatar);

        await SecureStore.setItemAsync(USER_KEY, JSON.stringify(freshUser));
        await SecureStore.setItemAsync(AVATAR_KEY, JSON.stringify(freshAvatar));
      } catch {
        await SecureStore.deleteItemAsync(TOKEN_KEY);
        await SecureStore.deleteItemAsync(USER_KEY);
        await SecureStore.deleteItemAsync(AVATAR_KEY);
        setToken(null);
        setUser(null);
        setAvatarProfile(DEFAULT_AVATAR_PROFILE);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const hydrateFullSession = async (accessToken: string, currentUser: AppUser) => {
    const avatar = await getAvatarProfileRequest(accessToken);

    setToken(accessToken);
    setUser(currentUser);
    setAvatarProfile(avatar);

    await SecureStore.setItemAsync(TOKEN_KEY, accessToken);
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(currentUser));
    await SecureStore.setItemAsync(AVATAR_KEY, JSON.stringify(avatar));
  };

  const signIn = async (username: string, password: string) => {
    const auth = await loginRequest(username, password);
    await hydrateFullSession(auth.access_token, auth.user);
  };

  const signUp = async (
    displayName: string,
    username: string,
    password: string
  ) => {
    const auth = await registerRequest(displayName, username, password);
    await hydrateFullSession(auth.access_token, auth.user);
  };

  const signOut = async () => {
    setToken(null);
    setUser(null);
    setAvatarProfile(DEFAULT_AVATAR_PROFILE);

    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_KEY);
    await SecureStore.deleteItemAsync(AVATAR_KEY);
  };

  const refreshSession = async () => {
    if (!token) return;

    const freshUser = await getCurrentUser(token);
    const freshAvatar = await getAvatarProfileRequest(token);

    setUser(freshUser);
    setAvatarProfile(freshAvatar);

    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(freshUser));
    await SecureStore.setItemAsync(AVATAR_KEY, JSON.stringify(freshAvatar));
  };

  const updateFriendPreferences = async (
    payload: UpdateFriendPreferencesPayload
  ) => {
    if (!token) {
      throw new Error("No hay sesión activa.");
    }

    const updatedUser = await updateFriendPreferencesRequest(token, payload);
    setUser(updatedUser);

    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(updatedUser));
  };

  const updateAvatarProfile = async (
    payload: UpdateAvatarPayload
  ) => {
    if (!token) {
      throw new Error("No hay sesión activa.");
    }

    const updatedAvatar = await updateAvatarProfileRequest(token, payload);
    setAvatarProfile(updatedAvatar);

    await SecureStore.setItemAsync(AVATAR_KEY, JSON.stringify(updatedAvatar));
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      avatarProfile,
      isLoading,
      signIn,
      signUp,
      signOut,
      refreshSession,
      updateFriendPreferences,
      updateAvatarProfile,
    }),
    [user, token, avatarProfile, isLoading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider.");
  }

  return context;
}