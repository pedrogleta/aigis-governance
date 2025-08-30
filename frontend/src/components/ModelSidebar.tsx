import React, { useEffect, useState } from 'react';
import { cn } from '../lib/utils';
import { apiService } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  open: boolean;
  onClose: () => void;
}

const ModelSidebar: React.FC<Props> = ({ open, onClose }) => {
  const [modelsMap, setModelsMap] = useState<
    Record<string, { description: string; available: boolean }>
  >({});
  const [current, setCurrent] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    let mounted = true;
    (async () => {
      try {
        const data = await apiService.getModels();
        if (!mounted) return;
        setModelsMap(data.models || {});
        if (data.current) setCurrent(data.current);
      } catch (e) {
        setError((e as Error).message);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [open]);

  const handleSelect = async (name: string) => {
    setBusy(true);
    setError(null);
    try {
      const selected = await apiService.selectModel(name);
      setCurrent(selected);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-20">
          <motion.div
            className="absolute inset-0 bg-black/50"
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.8 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ cursor: 'pointer' }}
          />
          <motion.div
            id="models-sidebar"
            className={cn(
              'absolute right-0 top-0 h-full w-full sm:w-[380px] bg-gray-900 border-l border-gray-800 p-4 overflow-y-auto',
            )}
            role="dialog"
            aria-modal="true"
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{
              type: 'spring',
              stiffness: 320,
              damping: 34,
              mass: 0.6,
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">LLM Model</h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-200 cursor-pointer"
              >
                Close
              </button>
            </div>

            {error && <div className="mb-3 text-xs text-red-400">{error}</div>}

            <div className="space-y-2">
              {Object.entries(modelsMap).map(([name, meta]) => {
                const availableFlag = !!meta.available;
                return (
                  <button
                    key={name}
                    onClick={() => availableFlag && handleSelect(name)}
                    disabled={busy || !availableFlag}
                    className={cn(
                      'w-full text-left border border-gray-800 rounded p-3 transition-colors',
                      availableFlag
                        ? 'hover:border-green-600'
                        : 'opacity-50 cursor-not-allowed',
                      current === name && 'border-green-600 bg-gray-800',
                    )}
                    style={{
                      cursor: availableFlag ? 'pointer' : 'not-allowed',
                    }}
                  >
                    <div className="text-sm text-white font-medium flex items-center gap-2">
                      <span>{name}</span>
                      {!availableFlag && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-gray-800 text-red-400 border border-gray-700">
                          Unavailable
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-400">
                      {meta.description}
                    </div>
                    {current === name && (
                      <div className="text-xs text-green-400 mt-1">
                        Selected
                      </div>
                    )}
                  </button>
                );
              })}
              {Object.keys(modelsMap).length === 0 && (
                <div className="text-xs text-gray-400">
                  No models discovered.
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default ModelSidebar;
