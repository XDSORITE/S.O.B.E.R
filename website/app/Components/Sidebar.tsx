import{
    FaMapMarkedAlt,
    FaCar,
    FaExclamationTriangle,
    FaChartBar,
    FaCog,
} from "react-icons/fa";
export default function Sidebar() {
    return(
        <div className="w-72 bg-[#111827] border-r border-white/10 p-6">
            <h1 className="text-3xl font-bold mb-10">
                DUI Sheild
            </h1>
            <div className="space-y-6 text-lg">
                <div className="flex items-center gap-3">
                    <FaMapMarkedAlt />
                    <span>Risk Map</span>
                </div>
                <div className="flex items-center gap-3">
                    <FaCar />
                    <span>Drivers</span>
                </div>
                <div className="flex items-center gap-3">
                    <FaExclamationTriangle />
                    <span>Alerts</span>
                </div>
                <div className="flex items-center gap-3">
                    <FaChartBar />
                    <span>Analytics</span>
                </div>
                <div className="flex items-center gap-3">
                    <FaCog />
                    <span>Settings</span>
                </div>
            </div>
        </div>
    );
}