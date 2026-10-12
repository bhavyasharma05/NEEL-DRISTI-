import React from 'react';
import { motion } from 'framer-motion';
import { BeakerIcon, GlobeAltIcon, ChartBarIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import Sidebar from '../components/Sidebar';
import OceanWave from '../components/OceanWave';

const About: React.FC = () => {
  const timelineData = [
    { year: '2023', event: 'Data Ingestion & Processing', description: 'Fetch and preprocess ARGO float data from public sources.' },
    { year: '2023', event: 'AI Integration', description: 'Implemented machine learning algorithms for pattern recognition in ocean data' },
    { year: '2024', event: 'Platform Launch', description: 'Beta version launched with basic ARGO float data visualization' },
    { year: '2024', event: 'Enhanced Features', description: 'Added interactive maps, chatbot, and advanced analytics capabilities' },
  ];

  const teamMembers = [
    { name: 'Bhavya Kumar Sharma', role: 'Backend devloper', icon: '🌊' },
    { name: 'Nishchal Kumar', role: 'Database Engineer', icon: '🤖' },
    { name: 'A.V Naga Venu', role: 'AI/ML Engineer', icon: '📊' },
    { name: 'Bhoomika', role: 'Front-end devloper', icon: '💻' },
    { name: 'Dimple', role: 'UI/UX Designer', icon: '💻' },
    { name: 'Mayank', role: 'Researcher', icon: '🌊' },
  ];

  const features = [
    {
      icon: BeakerIcon,
      title: 'Scientific Accuracy',
      description: 'All data is sourced directly from the ARGO float network, ensuring scientific accuracy and reliability.',
    },
    {
      icon: GlobeAltIcon,
      title: ' Indian ocean Coverage',
      description: 'Access to worldwide ocean data from over 3,800 active ARGO floats across all major ocean basins.',
    },
    {
      icon: ChartBarIcon,
      title: 'Advanced Analytics',
      description: 'AI-powered insights and pattern recognition to help researchers discover new oceanographic phenomena.',
    },
    {
      icon: UserGroupIcon,
      title: 'Community Driven',
      description: 'Built for researchers, by researchers, with continuous feedback from the marine science community.',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-[#001f3f] text-white">
      <Sidebar />
      
      <div className="ml-64 p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <h1 className="text-4xl font-bold mb-4">About Neel Drishti</h1>
          <p className="text-xl text-slate-300 max-w-4xl leading-relaxed">
          Neel Drishti is an AI-powered platform that makes ocean data accessible to everyone — researchers, educators, and enthusiasts alike — enabling them to easily explore and understand our  marine systems using ARGO float data.
          </p>
        </motion.div>

        {/* Mission Section */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-16"
        >
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold mb-6 text-[#00bcd4]">Our Mission</h2>
              <p className="text-slate-300 leading-relaxed mb-6">
                We believe that ocean data should be accessible to everyone. By combining the power of artificial intelligence
                with comprehensive ARGO float datasets, we're creating tools that help researchers understand ocean patterns,
                climate change impacts, and marine ecosystem dynamics.
              </p>
              <p className="text-slate-300 leading-relaxed">
                Our platform transforms complex oceanographic data into intuitive visualizations and insights,
                enabling discoveries that were previously only possible with extensive technical expertise.
              </p>
            </div>
            <div className="relative">
              <div className="w-full h-64 bg-gradient-to-br from-[#00bcd4] to-[#001f3f] rounded-xl flex items-center justify-center">
                <div className="text-6xl">🌊</div>
              </div>
              <OceanWave className="absolute -bottom-4 left-0 right-0 h-8" />
            </div>
          </div>
        </motion.section>

        {/* Features Grid */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold mb-8 text-center">Why Choose Neel Drishti?</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 hover:bg-white/20 transition-all duration-300"
              >
                <feature.icon className="h-12 w-12 text-[#00bcd4] mb-4" />
                <h3 className="text-lg font-semibold mb-3">{feature.title}</h3>
                <p className="text-sm text-slate-400">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* Timeline */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold mb-8 text-center">Development Timeline</h2>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-px bg-gradient-to-b from-[#00bcd4] to-transparent"></div>
            <div className="space-y-8">
              {timelineData.map((item, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.7 + index * 0.1 }}
                  className="relative pl-12"
                >
                  <div className="absolute left-0 w-8 h-8 bg-[#00bcd4] rounded-full flex items-center justify-center border-4 border-slate-900">
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                  <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                    <div className="flex items-center gap-4 mb-2">
                      <span className="px-3 py-1 bg-[#00bcd4] text-white rounded-full text-sm font-semibold">
                        {item.year}
                      </span>
                      <h3 className="text-xl font-semibold">{item.event}</h3>
                    </div>
                    <p className="text-slate-300">{item.description}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.section>

        {/* Team Section */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold mb-8 text-center">Our Team</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {teamMembers.map((member, index) => (
              <motion.div
                key={member.name}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.9 + index * 0.1 }}
                className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 text-center hover:bg-white/20 transition-all duration-300"
              >
                <div className="text-4xl mb-4">{member.icon}</div>
                <h3 className="text-lg font-semibold mb-2">{member.name}</h3>
                <p className="text-sm text-[#00bcd4]">{member.role}</p>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* Statistics */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="bg-gradient-to-r from-[#00bcd4]/20 to-[#001f3f]/20 rounded-2xl p-8 border border-[#00bcd4]/30"
        >
          <h2 className="text-2xl font-bold mb-8 text-center">Platform Impact</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
            {[
              { value: 'Testing phase', label: 'Data Visualizations Created' },
              { value: 'Testing phase', label: 'Research Papers Supported' },
              { value: 'Testing phase', label: 'Universities Using Platform' },
              { value: '99.9%', label: 'Platform Uptime' },
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.1 + index * 0.1 }}
              >
                <div className="text-3xl font-bold text-[#00bcd4] mb-2">{stat.value}</div>
                <div className="text-sm text-slate-400">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.section>
      </div>
    </div>
  );
};

export default About;