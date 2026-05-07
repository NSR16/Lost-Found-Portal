import { MapPin, Calendar, Tag, AlertTriangle, CheckCircle2 } from "lucide-react";

function formatDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

const TYPE_STYLE = {
  LOST: {
    badge: "badge-error",
    label: "Lost",
    icon: <AlertTriangle size={12} />,
  },
  FOUND: {
    badge: "badge-success",
    label: "Found",
    icon: <CheckCircle2 size={12} />,
  },
};

export default function ItemCard({ item, onClaim }) {
  const type = TYPE_STYLE[item.type] ?? TYPE_STYLE.LOST;
  const imageSrc = item.image_url ? `http://localhost:8000/uploads/${item.image_url}` : null;

  return (
    <div className="card bg-base-100 shadow-md hover:shadow-lg transition-shadow duration-200 border border-base-200">
      {/* Image or placeholder */}
      <figure className="h-40 bg-base-200 overflow-hidden rounded-t-2xl">
        {imageSrc ? (
          <img
            src={imageSrc}
            alt={item.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-base-content/30">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-14 h-14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}
      </figure>

      <div className="card-body p-4 gap-2">
        {/* Type badge + title */}
        <div className="flex items-start justify-between gap-2">
          <h2 className="card-title text-base font-semibold leading-tight line-clamp-1">
            {item.title}
          </h2>
          <span className={`badge badge-sm gap-1 shrink-0 ${type.badge}`}>
            {type.icon} {type.label}
          </span>
        </div>

        {/* Description */}
        {item.description && (
          <p className="text-sm text-base-content/60 line-clamp-2">
            {item.description}
          </p>
        )}

        {/* Meta info */}
        <div className="flex flex-col gap-1 mt-1">
          {item.category_name && (
            <span className="flex items-center gap-1 text-xs text-base-content/50">
              <Tag size={12} /> {item.category_name}
            </span>
          )}
          {item.location && (
            <span className="flex items-center gap-1 text-xs text-base-content/50">
              <MapPin size={12} /> {item.location}
            </span>
          )}
          <span className="flex items-center gap-1 text-xs text-base-content/50">
            <Calendar size={12} /> {formatDate(item.posted_at)}
          </span>
        </div>

        {/* Action */}
        <div className="card-actions mt-3">
          <button
            className="btn btn-primary btn-sm w-full"
            onClick={() => onClaim(item)}
          >
            {item.type === "FOUND" ? "Claim This Item" : "I Found This"}
          </button>
        </div>
      </div>
    </div>
  );
}
