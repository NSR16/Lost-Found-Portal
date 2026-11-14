import { useState } from "react";
import {
  ClipboardList,
  FilePlus2,
  GraduationCap,
  LogOut,
  Menu,
  Search,
  X,
} from "lucide-react";

const SECTIONS = [
  { id: "browse", label: "Browse Items", icon: Search },
  { id: "report", label: "Report Item", icon: FilePlus2 },
  { id: "claims", label: "My Claims", icon: ClipboardList },
];

export default function Navbar({
  search,
  onSearch,
  activeSection,
  onSectionChange,
  myClaimsCount,
  onLogout,
  currentUser,
}) {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  const selectSection = (section) => {
    onSectionChange(section);
    setMobileSidebarOpen(false);
  };

  return (
    <>
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-base-200 bg-base-100 shadow-sm transition-transform duration-200 lg:translate-x-0 ${
          mobileSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        aria-label="Main sidebar"
      >
        <div className="flex h-20 items-center gap-3 border-b border-base-200 px-6">
          <GraduationCap className="shrink-0 text-primary" size={30} />
          <span className="text-xl font-bold tracking-tight text-primary">
            CampusLink
          </span>
        </div>

        <nav className="flex-1 space-y-2 px-4 py-8" aria-label="Dashboard navigation">
          {SECTIONS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              className={`btn min-h-12 w-full justify-start gap-3 rounded-xl border-0 px-4 ${
                activeSection === id
                  ? "bg-[#4EA5AD] text-white hover:bg-[#428f96]"
                  : "bg-transparent text-base-content/70 hover:bg-base-200"
              }`}
              aria-current={activeSection === id ? "page" : undefined}
              onClick={() => selectSection(id)}
            >
              <Icon size={18} />
              <span className="flex-1 text-left">{label}</span>
              {id === "claims" && myClaimsCount > 0 && (
                <span className={`badge badge-sm border-0 ${
                  activeSection === id ? "bg-white/20 text-white" : "badge-ghost"
                }`}>
                  {myClaimsCount}
                </span>
              )}
            </button>
          ))}
        </nav>

        <div className="border-t border-base-200 p-4">
          <p
            className="mb-3 truncate px-2 text-sm text-base-content/70"
            title={`Welcome, ${currentUser?.name || "Campus member"}`}
          >
            Welcome, <span className="font-semibold text-base-content">{currentUser?.name || "Campus member"}</span>
          </p>
          <button
            type="button"
            className="btn btn-outline btn-error w-full gap-2"
            onClick={onLogout}
          >
            <LogOut size={17} />
            Logout
          </button>
        </div>
      </aside>

      {mobileSidebarOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/30 lg:hidden"
          aria-label="Close navigation menu"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      <header className="fixed left-0 right-0 top-0 z-30 flex h-16 items-center gap-3 border-b border-base-200 bg-base-100 px-4 shadow-sm lg:left-64 lg:px-8">
        <button
          type="button"
          className="btn btn-ghost btn-square shrink-0 lg:hidden"
          aria-label={mobileSidebarOpen ? "Close navigation menu" : "Open navigation menu"}
          onClick={() => setMobileSidebarOpen((open) => !open)}
        >
          {mobileSidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <label className="input input-bordered flex h-10 w-full max-w-2xl items-center gap-3">
          <Search size={18} className="shrink-0 text-base-content/50" />
          <input
            type="search"
            className="grow"
            placeholder="Search items..."
            value={search}
            onChange={(event) => onSearch(event.target.value)}
            aria-label="Search items"
          />
        </label>
      </header>
    </>
  );
}
