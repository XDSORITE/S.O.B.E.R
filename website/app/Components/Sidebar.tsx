"use client";
import {
    FaMapMarkedAlt,
    FaCar,
    FaExclamationTriangle,
    FaChartBar,
    FaCog,
    FaHome,
} from "react-icons/fa";
type Props = {
    active: string;
    setActive: (value: string) => void;
};
export default function Sidebar({active, setActive,}: Props) {
    const items = [
        { name: "Dashboard", icon: <FaHome /> },
        { name: "Risk Map", icon: <FaMapMarkedAlt /> },
        { name: "Drivers", icon: <FaCar /> },
        { name: "Alerts", icon: <FaExclamationTriangle /> },
        { name: "Analytics", icon: <FaChartBar /> },
        { name: "Settings", icon: <FaCog /> }
    ];
    return (
         <div className="w-72 bg-[#0F172A] border-r border-white/10 p-6 flex flex-col justify-between">
            <div>
                <h1 className="text-3x1 font-bold mb-10 text-blue-400">DUI Shield</h1>
                <div className="space-y-3">
                    {items.map((item) => (
                        <button key={item.name} onClick={() => setActive(item.name)} className={`w-full flex items-center gap-3 px-4 py-4 rounded-x1 transition-all duration-300 ${active === item.name? "bg-blue-500/20 border border-blue-500/30 text-blue-400" : "hover:bg-white/5 text-gray-300"}`}>
                            {item.icon}
                            <span>{item.name}</span>
                        </button>
                    ))}
                </div>
            </div>
            <div className="bg-green-500/10 border border-green-500/20 rounded-x1 p-4">
                <p className="text-green-400 font-semibold">System Online</p>
                <p className="text-sm text-gray-400">All systems operational</p>
            </div>
         </div>
    );
}