"use client";
import "./index.css";
import AuthWrapper from "./components/auth-wrapper";
import MultiListApp from "./components/multi-list/MultiListApp";

function Content() {
  return <MultiListApp />;
}

export default function App() {
  return <AuthWrapper Content={Content} />;
}
