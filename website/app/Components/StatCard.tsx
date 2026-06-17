type Props = {
  title: string;
  value: string;
  change: string;
  color: string;
};

export default function StatCard({
  title,
  value,
  change,
  color,
}: Props) {
  return (
    <div
      className="rounded-3xl p-6 border border-white/10 bg-[#0F172A] relative overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:border-blue-500/30"
    >
      <div
        className={`absolute inset-0 opacity-10 blur-3xl ${color}`}
      />

      <div className="relative z-10">
        <p className="text-gray-400 text-sm mb-3">
          {title}
        </p>

        <h2 className="text-4xl font-bold mb-2">
          {value}
        </h2>

        <p className="text-green-400 text-sm">
          {change}
        </p>
      </div>
    </div>
  );
}