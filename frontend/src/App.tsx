import { Routes, Route, Link, NavLink } from "react-router-dom";
import Home from "./pages/Home";
import NewEval from "./pages/NewEval";
import Results from "./pages/Results";
import History from "./pages/History";

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
          isActive
            ? "bg-gray-800 text-white"
            : "text-gray-400 hover:text-white hover:bg-gray-800"
        }`
      }
    >
      {children}
    </NavLink>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <nav className="bg-gray-900 border-b border-gray-800">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <Link
              to="/"
              className="text-lg font-bold text-white tracking-tight hover:text-gray-200 transition-colors"
            >
              BenchBro
            </Link>
            <div className="flex items-center gap-1">
              <NavItem to="/">Dashboard</NavItem>
              <NavItem to="/new">New Eval</NavItem>
              <NavItem to="/history">History</NavItem>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/new" element={<NewEval />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </main>
    </div>
  );
}
