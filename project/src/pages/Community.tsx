import React, { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import Sidebar from '../components/Sidebar';
import FloatingBubbles from '../components/FloatingBubbles';
import { PlusIcon, TrashIcon, NewspaperIcon, AcademicCapIcon, GlobeAltIcon } from '@heroicons/react/24/outline';

interface Community {
  id: string;
  name: string;
  description: string;
  createdAt: number;
}

const seedNews = [
  { title: 'El Niño conditions easing across Pacific', source: 'NOAA', url: '#' },
  { title: 'ARGO network reaches new coverage milestone', source: 'Argo Program', url: '#' },
];

const seedArticles = [
  { title: 'Decadal trends in upper ocean heat content', journal: 'Nature Climate Change', url: '#' },
  { title: 'Salinity patterns and freshwater fluxes', journal: 'Journal of Geophysical Research', url: '#' },
];

const seedPapers = [
  { title: 'Biogeochemical Argo: Observations for ocean biology', venue: 'Frontiers in Marine Science', url: '#' },
  { title: 'Global variability of mixed layer depth', venue: 'Deep Sea Research', url: '#' },
];

const CommunityPage: React.FC = () => {
  const [communities, setCommunities] = useState<Community[]>(() => {
    const raw = localStorage.getItem('neelDrishti_communities');
    return raw ? JSON.parse(raw) : [];
  });
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [activeTab, setActiveTab] = useState<'news' | 'articles' | 'papers'>('news');

  const save = (list: Community[]) => {
    setCommunities(list);
    localStorage.setItem('neelDrishti_communities', JSON.stringify(list));
  };

  const createCommunity = () => {
    if (!name.trim()) return;
    const item: Community = {
      id: crypto.randomUUID(),
      name: name.trim(),
      description: description.trim(),
      createdAt: Date.now(),
    };
    save([item, ...communities]);
    setName('');
    setDescription('');
  };

  const removeCommunity = (id: string) => {
    save(communities.filter(c => c.id !== id));
  };

  const content = useMemo(() => ({ news: seedNews, articles: seedArticles, papers: seedPapers }), []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-[#001f3f] text-white relative overflow-hidden">
      <FloatingBubbles />
      <Sidebar />

      <div className="ml-64 p-8 h-screen overflow-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
          <h1 className="text-4xl font-bold mb-2">Community</h1>
          <p className="text-slate-400">Create topic-focused groups and browse oceanography news, articles, and papers.</p>
        </motion.div>

        {/* Create community */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white/10 backdrop-blur-sm rounded-xl border border-white/20 p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Create a Community</h2>
          <div className="grid md:grid-cols-3 gap-3">
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Community name" className="px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:border-[#00bcd4] focus:outline-none" />
            <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Short description" className="px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:border-[#00bcd4] focus:outline-none" />
            <button onClick={createCommunity} className="px-4 py-2 bg-gradient-to-r from-[#00bcd4] to-[#00acc1] rounded-lg flex items-center justify-center gap-2 hover:shadow-lg">
              <PlusIcon className="h-4 w-4" /> Create
            </button>
          </div>
        </motion.div>

        {/* Communities list */}
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20 p-6">
            <h3 className="text-lg font-semibold mb-4">Your Communities</h3>
            {communities.length === 0 ? (
              <p className="text-slate-400">No communities yet. Create one above.</p>
            ) : (
              <div className="space-y-3">
                {communities.map(c => (
                  <div key={c.id} className="flex items-start justify-between bg-white/5 rounded-lg p-4 border border-white/10">
                    <div>
                      <div className="font-semibold">{c.name}</div>
                      <div className="text-sm text-slate-300">{c.description || 'No description'}</div>
                      <div className="text-xs text-slate-400 mt-1">Created {new Date(c.createdAt).toLocaleString()}</div>
                    </div>
                    <button onClick={() => removeCommunity(c.id)} className="px-3 py-2 bg-red-600/80 hover:bg-red-600 rounded-lg flex items-center gap-2">
                      <TrashIcon className="h-4 w-4" /> Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Content tabs */}
          <div className="bg-white/10 backdrop-blur-sm rounded-xl border border-white/20 p-6">
            <h3 className="text-lg font-semibold mb-4">Discover</h3>
            <div className="flex gap-2 mb-4">
              <button onClick={() => setActiveTab('news')} className={`px-3 py-1 rounded-full border ${activeTab === 'news' ? 'bg-[#00bcd4] border-[#00bcd4]' : 'bg-white/5 border-white/10'}`}>
                <GlobeAltIcon className="h-4 w-4 inline mr-1" /> News
              </button>
              <button onClick={() => setActiveTab('articles')} className={`px-3 py-1 rounded-full border ${activeTab === 'articles' ? 'bg-[#00bcd4] border-[#00bcd4]' : 'bg-white/5 border-white/10'}`}>
                <NewspaperIcon className="h-4 w-4 inline mr-1" /> Articles
              </button>
              <button onClick={() => setActiveTab('papers')} className={`px-3 py-1 rounded-full border ${activeTab === 'papers' ? 'bg-[#00bcd4] border-[#00bcd4]' : 'bg-white/5 border-white/10'}`}>
                <AcademicCapIcon className="h-4 w-4 inline mr-1" /> Papers
              </button>
            </div>
            <div className="space-y-3">
              {content[activeTab].map((item: any, idx: number) => (
                <a key={idx} href={item.url} className="block bg-white/5 rounded-lg p-4 border border-white/10 hover:bg-white/10">
                  <div className="font-medium">{item.title}</div>
                  <div className="text-xs text-slate-400">{item.source || item.journal || item.venue}</div>
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommunityPage;


