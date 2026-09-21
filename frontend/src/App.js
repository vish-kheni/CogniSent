import React, { useState } from "react";
import { AppProvider } from "./context/AppContext";
import Navbar from "./components/Layout/Navbar";
import Footer from "./components/Layout/Footer";
import Dashboard from "./components/Dashboard/Dashboard";
import ReviewInput from "./components/ReviewInput/ReviewInput";

function AppShell() {
  const [activeTab, setActiveTab] = useState("analyze");

  const renderTab = () => {
    switch (activeTab) {
      case "analyze":
        return <ReviewInput />;
      case "dashboard":
        return <Dashboard onNavigate={setActiveTab} />;
      default:
        return <ReviewInput />;
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-beige font-body text-ink">
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">{renderTab()}</main>
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  );
}
