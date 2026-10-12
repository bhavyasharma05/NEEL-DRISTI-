import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ChevronRightIcon, PlayIcon } from '@heroicons/react/24/outline';
import OceanWave from '../components/OceanWave';
import FloatingBubbles from '../components/FloatingBubbles';

const Landing: React.FC = () => {
  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-b from-[#001f3f] via-slate-900 to-[#001f3f]">
      <FloatingBubbles />
      
      {/* Navigation */}
      <motion.nav
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="relative z-20 flex justify-between items-center p-6"
      >
        <div className="text-2xl font-bold text-[#00bcd4]">Neel Drishti</div>
        <div className="flex space-x-6">
          <Link
            to="/login"
            className="text-slate-300 hover:text-[#00bcd4] transition-colors"
          >
            Login
          </Link>
          <Link
            to="/register"
            className="px-4 py-2 bg-[#00bcd4] text-white rounded-lg hover:bg-[#00acc1] transition-colors"
          >
            Get Started
          </Link>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl"
        >
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Democratizing Access to{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00bcd4] to-[#ff7043]">
              Ocean Data
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-slate-300 mb-8 max-w-3xl mx-auto">
            Harness the power of AI to explore and analyze ARGO float data from across the world's oceans.
            Discover insights that drive marine research forward.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              to="/login"
              className="group px-8 py-4 bg-gradient-to-r from-[#00bcd4] to-[#00acc1] text-white rounded-full font-semibold flex items-center hover:shadow-lg hover:shadow-[#00bcd4]/25 transition-all duration-300"
            >
              Get Started
              <ChevronRightIcon className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <button className="group px-8 py-4 border-2 border-[#00bcd4] text-[#00bcd4] rounded-full font-semibold flex items-center hover:bg-[#00bcd4] hover:text-white transition-all duration-300">
              <PlayIcon className="mr-2 h-5 w-5" />
              Watch Demo
            </button>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-4xl"
        >
          {[
            { value: '3,800+', label: 'Active ARGO Floats' },
            { value: '250M+', label: 'Data Points Collected' },
            { value: '120+', label: 'Countries Involved' },
          ].map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-[#00bcd4] mb-2">
                {stat.value}
              </div>
              <div className="text-slate-400">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Ocean Wave Animation */}
      <OceanWave className="absolute bottom-0 left-0 right-0 h-32" />

      {/* Features Preview */}
      <motion.section
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 1 }}
        className="relative z-10 py-20 px-6 bg-gradient-to-b from-transparent to-slate-900"
      >
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-white mb-16">
            Explore Ocean Data Like Never Before
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                title: 'AI-Powered Insights',
                description: 'Advanced machine learning algorithms analyze patterns in ocean temperature, salinity, and pressure data.',
                icon: '🤖',
              },
              {
                title: 'Interactive Maps',
                description: 'Visualize ARGO float locations and data in real-time with our interactive mapping system.',
                icon: '🗺️',
              },
              {
                title: 'Data Export',
                description: 'Export findings in multiple formats including CSV and NetCDF for further research.',
                icon: '📊',
              },
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ y: 50, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20"
              >
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold text-white mb-4">{feature.title}</h3>
                <p className="text-slate-300">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>
    </div>
  );
};

export default Landing;