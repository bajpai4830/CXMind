import React, { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Activity, LayoutDashboard, LogOut, Ticket, Menu, X } from "lucide-react";

export function DashboardLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="dashboardLayout">
      {/* Mobile Topbar */}
      <header className="mobileTopbar glassPanel">
        <div className="brandGroup">
          <div className="brandMark" aria-hidden="true" />
          <div className="brandName">CXMind</div>
        </div>
        <button className="btnIcon" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </header>

      {/* Sidebar */}
      <aside className={`sidebar glassPanel ${mobileMenuOpen ? "open" : ""}`}>
        <div className="sidebarHeader">
          <div className="brandMark" aria-hidden="true" />
          <div className="brandName">CXMind</div>
        </div>
        <nav className="sidebarNav">
          <div className="navLabel muted">Dashboards</div>
          {user?.role === "admin" && (
            <Link to="/admin" onClick={() => setMobileMenuOpen(false)} className={`navItem ${location.pathname === "/admin" ? "active" : ""}`}>
              <Activity size={18} />
              <span>Admin Analytics</span>
            </Link>
          )}
          <Link to="/dashboard" onClick={() => setMobileMenuOpen(false)} className={`navItem ${location.pathname === "/dashboard" ? "active" : ""}`}>
            <Ticket size={18} />
            <span>Workspace</span>
          </Link>
        </nav>
        <div className="sidebarFooter">
          <div className="userInfo muted">
            <span className="userEmail">{user?.email}</span>
            <span className={`tag tag-${user?.role === 'admin' ? 'positive' : 'neutral'}`}>{user?.role}</span>
          </div>
          <button className="btn navItem btnLogout" onClick={() => void handleLogout()}>
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="dashboardContent">
        <div className="scrollArea">
          <Outlet />
        </div>
      </main>
      
      {/* Mobile Backdrop */}
      {mobileMenuOpen && <div className="mobileBackdrop" onClick={() => setMobileMenuOpen(false)} />}
    </div>
  );
}
