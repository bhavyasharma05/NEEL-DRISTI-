import React from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import Sidebar from '../components/Sidebar';
import OceanWave from '../components/OceanWave';

const temperatureData = [
  { month: 'Jan', temp: 14.2 },
  { month: 'Feb', temp: 14.8 },
  { month: 'Mar', temp: 15.4 },
  { month: 'Apr', temp: 16.1 },
  { month: 'May', temp: 17.2 },
  { month: 'Jun', temp: 18.9 },
];

const salinityData = [
  { depth: 0, salinity: 35.2 },
  { depth: 50, salinity: 35.4 },
  { depth: 100, salinity: 35.6 },
  { depth: 200, salinity: 35.8 },
  { depth: 500, salinity: 34.9 },
  { depth: 1000, salinity: 34.7 },
];

const Dashboard: React.FC = () => {
  const kpiData = [
    { title: 'Average Temperature', value: '16.3°C', change: '+2.4%', color: 'from-orange-500 to-red-500' },
    { title: 'Average Salinity', value: '35.2 PSU', change: '-0.1%', color: 'from-blue-500 to-cyan-500' },
    { title: 'Active Floats', value: '3,847', change: '+12', color: 'from-green-500 to-emerald-500' },
    { title: 'Data Points Today', value: '24.7K', change: '+8.3%', color: 'from-purple-500 to-pink-500' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-[#001f3f] text-white">
      <Sidebar />
      
      <div className="ml-64 p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold mb-2">Ocean Data Dashboard</h1>
          <p className="text-slate-400">Real-time insights from ARGO float network</p>
        </motion.div>

        {/* KPI Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          {kpiData.map((kpi, index) => (
            <motion.div
              key={kpi.title}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 hover:bg-white/20 transition-all duration-300"
            >
              <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${kpi.color} mb-4 flex items-center justify-center`}>
                <div className="w-6 h-6 bg-white/30 rounded-full"></div>
              </div>
              <h3 className="text-sm text-slate-400 mb-1">{kpi.title}</h3>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold">{kpi.value}</span>
                <span className={`text-sm ${kpi.change.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
                  {kpi.change}
                </span>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20"
          >
            <h3 className="text-xl font-semibold mb-4">Temperature Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={temperatureData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="temp"
                  stroke="#00bcd4"
                  strokeWidth={3}
                  dot={{ fill: '#00bcd4', strokeWidth: 2, r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20"
          >
            <h3 className="text-xl font-semibold mb-4">Salinity by Depth</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={salinityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="depth" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="salinity"
                  stroke="#ff7043"
                  fill="url(#salinityGradient)"
                />
                <defs>
                  <linearGradient id="salinityGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ff7043" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#ff7043" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Ocean Wave Transition */}
        <div className="mt-12 mb-8">
          <OceanWave className="h-16 rounded-xl" />
        </div>

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20"
        >
          <h3 className="text-xl font-semibold mb-6">Recent Float Activity</h3>
          <div className="space-y-4">
            {[
              { id: 'ARGO_5904623', location: 'North Atlantic', status: 'Data Received', time: '2 minutes ago' },
              { id: 'ARGO_5904587', location: 'Pacific Ocean', status: 'Surfaced', time: '15 minutes ago' },
              { id: 'ARGO_5904591', location: 'Indian Ocean', status: 'Diving', time: '1 hour ago' },
            ].map((activity, index) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.9 + index * 0.1 }}
                className="flex items-center justify-between p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
              >
                <div>
                  <div className="font-semibold text-[#00bcd4]">{activity.id}</div>
                  <div className="text-sm text-slate-400">{activity.location}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">{activity.status}</div>
                  <div className="text-xs text-slate-500">{activity.time}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;