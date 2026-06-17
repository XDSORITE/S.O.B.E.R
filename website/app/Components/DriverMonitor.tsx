export default function DriverMonitor() {
  return (
    <div className="bg-[#0F172A] border border-white/10 rounded-3xl p-5">
      <h2 className="text-2xl font-bold mb-4">
        Driver Monitoring
      </h2>

      <div className="bg-black rounded-2xl h-40 flex items-center justify-center mb-5">
        <p className="text-gray-500">
          Live Camera Feed
        </p>
      </div>

      <div className="space-y-3">
        <p>Driver Status: Active</p>
        <p>Facial Tracking: Normal</p>
        <p>Drowsiness Level: 12%</p>
        <p>DUI Risk Score: 18%</p>
        <p>Vehicle Speed: 50 MPH</p>
      </div>
    </div>
  );
}