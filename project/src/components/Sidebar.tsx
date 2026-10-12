import React from 'react';
import { motion } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  ChartBarIcon,
  MapIcon,
  ChatBubbleLeftIcon,
  InformationCircleIcon,
  UserIcon,
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Insights', href: '/insights', icon: ChartBarIcon },
  { name: 'Maps', href: '/map', icon: MapIcon },
  { name: 'Chatbot', href: '/chatbot', icon: ChatBubbleLeftIcon },
  { name: 'Community', href: '/community', icon: ChatBubbleLeftIcon },
  { name: 'About', href: '/about', icon: InformationCircleIcon },
  { name: 'Profile', href: '#', icon: UserIcon },
];

const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <motion.div
      initial={{ x: -250 }}
      animate={{ x: 0 }}
      className="fixed left-0 top-0 h-full w-64 bg-gradient-to-b from-[#001f3f] to-slate-900 text-white p-6 z-40"
    >
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-[#00bcd4]">Neel Drishti</h2>
        <p className="text-sm text-slate-300 mt-1">devloped by Team Neel Drishti</p>
      </div>

      <nav className="space-y-2">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex items-center px-4 py-3 rounded-lg transition-all duration-200 ${isActive
                ? 'bg-[#00bcd4] text-white shadow-lg'
                : 'text-slate-300 hover:bg-slate-800 hover:text-[#00bcd4]'
                }`}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="absolute bottom-6 left-6 right-6">
        <div className="p-4 bg-slate-800 rounded-lg">
          <p className="text-xs text-slate-400 mb-2">Ocean Coverage</p>
          <div className="w-full bg-slate-700 rounded-full h-2">
            <motion.div
              className="bg-gradient-to-r from-[#00bcd4] to-[#ff7043] h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: '78%' }}
              transition={{ duration: 2, delay: 0.5 }}
            />
          </div>
          <p className="text-xs text-slate-300 mt-1">78% Complete</p>
        </div>
      </div>
    </motion.div>
  );
};

export default Sidebar;