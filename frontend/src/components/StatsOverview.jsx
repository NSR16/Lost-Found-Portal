import { PackageSearch, CheckCircle, AlertCircle } from "lucide-react";

const stats = [
  {
    label: "Total Items Lost",
    key: "totalLost",
    icon: <PackageSearch size={28} className="text-error" />,
    color: "bg-error/10 border-error/20",
    badge: "badge-error",
  },
  {
    label: "Recently Found",
    key: "totalFound",
    icon: <CheckCircle size={28} className="text-success" />,
    color: "bg-success/10 border-success/20",
    badge: "badge-success",
  },
  {
    label: "Active Claims",
    key: "activeClaims",
    icon: <AlertCircle size={28} className="text-warning" />,
    color: "bg-warning/10 border-warning/20",
    badge: "badge-warning",
  },
];

export default function StatsOverview({ data }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      {stats.map((s) => (
        <div
          key={s.key}
          className={`card border ${s.color} shadow-sm`}
        >
          <div className="card-body flex-row items-center gap-4 py-5">
            <div className="p-3 rounded-xl bg-base-100 shadow-sm">
              {s.icon}
            </div>
            <div>
              <p className="text-sm text-base-content/60 font-medium">
                {s.label}
              </p>
              <p className="text-3xl font-bold text-base-content">
                {data?.[s.key] ?? "—"}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
