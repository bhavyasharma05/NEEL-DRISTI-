import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { MapPinIcon, InformationCircleIcon } from '@heroicons/react/24/outline';
import Sidebar from '../components/Sidebar';

// Mock ARGO float data
const argoFloats = [
  { id: 'ARGO_5904623', lat: 35.2, lng: -42.1, status: 'active', temp: 16.3, salinity: 35.2, lastUpdate: '2 hours ago' },
  { id: 'ARGO_5904587', lat: 28.5, lng: -38.7, status: 'active', temp: 18.1, salinity: 35.4, lastUpdate: '1 hour ago' },
  { id: 'ARGO_5904591', lat: -15.3, lng: 67.8, status: 'diving', temp: 14.2, salinity: 34.9, lastUpdate: '3 hours ago' },
  { id: 'ARGO_5904612', lat: 42.1, lng: -28.3, status: 'surfaced', temp: 12.8, salinity: 35.1, lastUpdate: '30 minutes ago' },
  { id: 'ARGO_5904634', lat: -5.2, lng: 15.4, status: 'active', temp: 19.5, salinity: 35.6, lastUpdate: '45 minutes ago' },
];

const Map: React.FC = () => {
  const [selectedFloat, setSelectedFloat] = useState<typeof argoFloats[0] | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'diving': return 'bg-yellow-500';
      case 'surfaced': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-[#001f3f] text-white">
      <Sidebar />
      
      <div className="ml-64 p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold mb-2">ARGO Float Locations</h1>
          <p className="text-slate-400">Interactive map showing active ocean monitoring stations</p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Map Container */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-3 bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20"
          >
            <div className="relative w-full h-96 bg-gradient-to-b from-[#001f3f] to-[#003d5c] rounded-lg overflow-hidden">
              {/* Mock World Map Background */}
              <div className="absolute inset-0 opacity-20">
                <svg viewBox="0 0 1000 500" className="w-full h-full">
                  <path
                    d="M150,200 Q200,150 300,180 T500,200 T700,220 Q800,200 900,210"
                    stroke="#00bcd4"
                    strokeWidth="2"
                    fill="none"
                    opacity="0.5"
                  />
                  <path
                    d="M100,300 Q200,280 350,290 T600,310 T850,300"
                    stroke="#00bcd4"
                    strokeWidth="2"
                    fill="none"
                    opacity="0.3"
                  />
                </svg>
              </div>

              {/* ARGO Float Markers */}
              {argoFloats.map((float, index) => {
                const x = ((float.lng + 180) / 360) * 100;
                const y = ((90 - float.lat) / 180) * 100;
                
                return (
                  <motion.button
                    key={float.id}
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.5 + index * 0.1 }}
                    className={`absolute w-4 h-4 rounded-full ${getStatusColor(float.status)} border-2 border-white shadow-lg hover:scale-150 transition-transform duration-300`}
                    style={{
                      left: `${x}%`,
                      top: `${y}%`,
                      transform: 'translate(-50%, -50%)',
                    }}
                    onClick={() => setSelectedFloat(float)}
                  />
                );
              })}

              {/* Legend */}
              <div className="absolute bottom-4 left-4 bg-black/50 rounded-lg p-3">
                <div className="text-sm font-semibold mb-2">Float Status</div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    <span className="text-xs">Active</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <span className="text-xs">Diving</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                    <span className="text-xs">Surfaced</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Float Details Panel */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20"
          >
            <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <InformationCircleIcon className="h-5 w-5 text-[#00bcd4]" />
              Float Details
            </h3>

            {selectedFloat ? (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <div className="p-4 bg-white/10 rounded-lg">
                  <div className="font-semibold text-[#00bcd4] mb-2">{selectedFloat.id}</div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Status:</span>
                      <span className="capitalize">{selectedFloat.status}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Latitude:</span>
                      <span>{selectedFloat.lat}°</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Longitude:</span>
                      <span>{selectedFloat.lng}°</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Temperature:</span>
                      <span>{selectedFloat.temp}°C</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Salinity:</span>
                      <span>{selectedFloat.salinity} PSU</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Last Update:</span>
                      <span>{selectedFloat.lastUpdate}</span>
                    </div>
                  </div>
                </div>
                
                <button className="w-full px-4 py-2 bg-[#00bcd4] text-white rounded-lg hover:bg-[#00acc1] transition-colors">
                  View Full Profile
                </button>
              </motion.div>
            ) : (
              <div className="text-center text-slate-400">
                <MapPinIcon className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>Click on a float marker to view details</p>
              </div>
            )}
          </motion.div>
        </div>

        {/* Float List */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="mt-8 bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20"
        >
          <h3 className="text-xl font-semibold mb-4">Active ARGO Floats</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-600">
                  <th className="text-left py-3 px-4">Float ID</th>
                  <th className="text-left py-3 px-4">Location</th>
                  <th className="text-left py-3 px-4">Status</th>
                  <th className="text-left py-3 px-4">Temperature</th>
                  <th className="text-left py-3 px-4">Salinity</th>
                  <th className="text-left py-3 px-4">Last Update</th>
                </tr>
              </thead>
              <tbody>
                {argoFloats.map((float, index) => (
                  <motion.tr
                    key={float.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8 + index * 0.1 }}
                    className="border-b border-slate-700/50 hover:bg-white/5 cursor-pointer"
                    onClick={() => setSelectedFloat(float)}
                  >
                    <td className="py-3 px-4 font-mono text-[#00bcd4]">{float.id}</td>
                    <td className="py-3 px-4">{float.lat}°, {float.lng}°</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(float.status)} text-white`}>
                        {float.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">{float.temp}°C</td>
                    <td className="py-3 px-4">{float.salinity} PSU</td>
                    <td className="py-3 px-4 text-slate-400">{float.lastUpdate}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Map;