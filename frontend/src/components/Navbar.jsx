import { Search, PlusCircle, GraduationCap, LogOut } from "lucide-react";

export default function Navbar({ search, onSearch, onReport, onLogout, currentUser }) {
  return (
    <div className="navbar bg-base-100 shadow-md px-4 sticky top-0 z-50">
      {/* Brand */}
      <div className="navbar-start gap-2">
        <GraduationCap className="text-primary" size={28} />
        <span className="text-xl font-bold text-primary tracking-tight">
          CampusLink
        </span>
      </div>

      {/* Search bar */}
      <div className="navbar-center hidden md:flex">
        <label className="input input-bordered flex items-center gap-2 w-80">
          <Search size={16} className="text-base-content/50" />
          <input
            type="text"
            className="grow"
            placeholder="Search lost &amp; found items…"
            value={search}
            onChange={(e) => onSearch(e.target.value)}
          />
        </label>
      </div>

      {/* CTA Section */}
      <div className="navbar-end gap-2">
        {currentUser && (
          <div className="text-sm text-base-content/70 hidden md:block">
            Welcome, <span className="font-medium">{currentUser.name}</span>
          </div>
        )}
        <button
          className="btn btn-primary btn-sm gap-1"
          onClick={onReport}
        >
          <PlusCircle size={16} />
          Report Item
        </button>

        {/* Logout Button */}
        <button
          className="btn btn-outline btn-error btn-sm gap-1"
          onClick={onLogout}
        >
          <LogOut size={16} />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </div>
  );
}