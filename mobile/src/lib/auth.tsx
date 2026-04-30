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
  getCurrentUser,
  loginRequest,
  registerRequest,
  updateFriendPreferencesRequest,
  type UpdateFriendPreferencesPayload,
} from "./api";

const TOKEN_KEY = "mobile_access_token";
const USER_KEY = "mobile_user";

type AuthContextValue = {
  user: AppUser | null;
  token: string | null;
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
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const restoreSession = async () => {
      try {
        const savedToken = await SecureStore.getItemAsync(TOKEN_KEY);
        const savedUser = await SecureStore.getItemAsync(USER_KEY);

        if (!savedToken || !savedUser) {
          setIsLoading(false);
          return;
        }

        const parsedUser = JSON.parse(savedUser) as AppUser;

        setToken(savedToken);
        setUser(parsedUser);

        const freshUser = await getCurrentUser(savedToken);
        setUser(freshUser);
        await SecureStore.setItemAsync(USER_KEY, JSON.stringify(freshUser));
      } catch {
        await SecureStore.deleteItemAsync(TOKEN_KEY);
        await SecureStore.deleteItemAsync(USER_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const signIn = async (username: string, password: string) => {
    const auth = await loginRequest(username, password);
    setToken(auth.access_token);
    setUser(auth.user);

    await SecureStore.setItemAsync(TOKEN_KEY, auth.access_token);
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(auth.user));
  };

  const signUp = async (
    displayName: string,
    username: string,
    password: string
  ) => {
    const auth = await registerRequest(displayName, username, password);
    setToken(auth.access_token);
    setUser(auth.user);

    await SecureStore.setItemAsync(TOKEN_KEY, auth.access_token);
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(auth.user));
  };

  const signOut = async () => {
    setToken(null);
    setUser(null);

    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_KEY);
  };

  const refreshSession = async () => {
    if (!token) return;

    const freshUser = await getCurrentUser(token);
    setUser(freshUser);
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(freshUser));
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

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      signIn,
      signUp,
      signOut,
      refreshSession,
      updateFriendPreferences,
    }),
    [user, token, isLoading]
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