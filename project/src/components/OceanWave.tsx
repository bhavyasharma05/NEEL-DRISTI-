import React from 'react';
import { motion } from 'framer-motion';

interface OceanWaveProps {
  className?: string;
}

const OceanWave: React.FC<OceanWaveProps> = ({ className = '' }) => {
  return (
    <div className={`relative overflow-hidden ${className}`}>
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-[#001f3f] via-[#00bcd4] to-[#001f3f]"
        animate={{
          backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'linear',
        }}
        style={{
          backgroundSize: '200% 200%',
        }}
      />
      <motion.div
        className="absolute inset-0 opacity-60"
        animate={{
          transform: [
            'translateX(0%) scaleY(1)',
            'translateX(-100%) scaleY(1.2)',
            'translateX(-200%) scaleY(1)',
          ],
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      >
        <svg
          className="w-full h-full"
          viewBox="0 0 1200 120"
          preserveAspectRatio="none"
        >
          <path
            d="M0,60 C200,20 400,100 600,60 C800,20 1000,100 1200,60 L1200,120 L0,120 Z"
            fill="rgba(0,188,212,0.3)"
          />
        </svg>
      </motion.div>
    </div>
  );
};

export default OceanWave;