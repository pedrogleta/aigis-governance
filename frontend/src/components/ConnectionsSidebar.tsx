import React, { useEffect, useRef, useState } from 'react';
// icons not needed here
import { cn } from '../lib/utils';
import type { UserConnection, UserConnectionCreate } from '../services/api';
import ConfirmationModal from './ConfirmationModal';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  open: boolean;
  onClose: () => void;
  connections: UserConnection[];
  selectedConnection: UserConnection | null;
  formState: UserConnectionCreate;
  editingId: number | null;
  testingId: number | null;
  setFormState: (s: UserConnectionCreate) => void;
  setEditingId: (id: number | null) => void;
  onSelect: (c: UserConnection | null) => void;
  onSave: () => void;
  onEdit: (c: UserConnection) => void;
  onDelete: (id: number) => void;
  onTest: (id: number) => void;
  onRefresh: () => void;
}

const ConnectionsSidebar: React.FC<Props> = ({
  open,
  onClose,
  connections,
  selectedConnection,
  formState,
  editingId,
  testingId,
  setFormState,
  setEditingId,
  onSelect,
  onSave,
  onEdit,
  onDelete,
  onTest,
  onRefresh,
}) => {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null);

  const confirmDelete = (id: number) => {
    setPendingDeleteId(id);
    setConfirmOpen(true);
  };

  const handleConfirm = () => {
    if (pendingDeleteId != null) onDelete(pendingDeleteId);
    setPendingDeleteId(null);
    setConfirmOpen(false);
  };

  const handleCancel = () => {
    setPendingDeleteId(null);
    setConfirmOpen(false);
  };

  // simple focus trap: focus first input when opening
  const firstInputRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    if (open) firstInputRef.current?.focus();
  }, [open]);

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
            id="connections-sidebar"
            className={cn(
              'absolute right-0 top-0 h-full w-full sm:w-[420px] bg-gray-900 border-l border-gray-800 p-4 overflow-y-auto',
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
              <h2 className="text-lg font-semibold text-white">Connections</h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-200 cursor-pointer"
              >
                Close
              </button>
            </div>

            <div className="space-y-2 mb-6">
              <label className="block text-sm text-gray-300">Name</label>
              <input
                ref={firstInputRef}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                value={formState.name || ''}
                onChange={(e) =>
                  setFormState({ ...formState, name: e.target.value })
                }
                placeholder="My Postgres"
              />
              <label className="block text-sm text-gray-300 mt-3">Type</label>
              <select
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                value={formState.db_type}
                onChange={(e) =>
                  setFormState({
                    ...formState,
                    db_type: e.target.value as 'postgres' | 'sqlite',
                  })
                }
              >
                <option value="postgres">PostgreSQL</option>
                <option value="sqlite">SQLite</option>
              </select>

              {formState.db_type === 'sqlite' ? (
                <>
                  <label className="block text-sm text-gray-300 mt-3">
                    File path
                  </label>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    value={formState.host || ''}
                    onChange={(e) =>
                      setFormState({ ...formState, host: e.target.value })
                    }
                    placeholder="/path/to/db.sqlite"
                  />
                </>
              ) : (
                <>
                  <label className="block text-sm text-gray-300 mt-3">
                    Host
                  </label>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    value={formState.host || ''}
                    onChange={(e) =>
                      setFormState({ ...formState, host: e.target.value })
                    }
                    placeholder="localhost"
                  />
                  <label className="block text-sm text-gray-300 mt-3">
                    Port
                  </label>
                  <input
                    type="number"
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    value={formState.port || ''}
                    onChange={(e) =>
                      setFormState({
                        ...formState,
                        port: Number(e.target.value),
                      })
                    }
                    placeholder="5432"
                  />
                  <label className="block text-sm text-gray-300 mt-3">
                    Username
                  </label>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    value={formState.username || ''}
                    onChange={(e) =>
                      setFormState({ ...formState, username: e.target.value })
                    }
                    placeholder="postgres"
                  />
                  <label className="block text-sm text-gray-300 mt-3">
                    Database
                  </label>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    value={formState.database_name || ''}
                    onChange={(e) =>
                      setFormState({
                        ...formState,
                        database_name: e.target.value,
                      })
                    }
                    placeholder="example_db"
                  />
                  <label className="block text-sm text-gray-300 mt-3">
                    Password
                  </label>
                  <input
                    type="password"
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    onChange={(e) =>
                      setFormState({ ...formState, password: e.target.value })
                    }
                    placeholder={
                      editingId ? 'Leave blank to keep current' : 'Password'
                    }
                  />
                </>
              )}

              <div className="flex items-center space-x-2 mt-4">
                <button
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded cursor-pointer"
                  onClick={onSave}
                >
                  {editingId ? 'Update' : 'Create'}
                </button>
                <button
                  className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded cursor-pointer"
                  onClick={() => {
                    setEditingId(null);
                    setFormState({ name: '', db_type: 'postgres' });
                  }}
                >
                  Clear
                </button>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-2">
                Your connections
              </h3>
              <div className="space-y-2">
                {connections.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => onSelect(c)}
                    onKeyDown={(e: React.KeyboardEvent) => {
                      if (e.key === 'Enter' || e.key === ' ') onSelect(c);
                    }}
                    tabIndex={0}
                    role="button"
                    className={cn(
                      'border border-gray-800 rounded p-3 flex items-center justify-between space-x-3 hover:border-green-600 transition-colors',
                      selectedConnection?.id === c.id &&
                        'border-green-600 bg-gray-800',
                    )}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <input
                        type="radio"
                        name="connection"
                        checked={selectedConnection?.id === c.id}
                        onChange={() => onSelect(c)}
                        onClick={(e) => e.stopPropagation()}
                        aria-label={`Select connection ${c.name}`}
                        className="h-4 w-4 text-green-600 bg-gray-800 border-gray-700"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-white truncate">
                          {c.name}
                        </div>
                        <div className="text-xs text-gray-400 truncate">
                          {c.db_type} {c.host ? `• ${c.host}` : ''}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        title={
                          selectedConnection?.id === c.id
                            ? 'Selected'
                            : 'Select'
                        }
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect(c);
                        }}
                        className={cn(
                          'text-xs px-2 py-1 rounded text-gray-200 hover:bg-gray-800 transition-colors',
                          selectedConnection?.id === c.id &&
                            'bg-green-600 text-white',
                        )}
                        style={{ cursor: 'pointer' }}
                      >
                        {selectedConnection?.id === c.id
                          ? 'Selected'
                          : 'Select'}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onTest(c.id);
                        }}
                        disabled={testingId === c.id}
                        className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-200 transition-colors"
                        style={{ cursor: 'pointer' }}
                      >
                        {testingId === c.id ? 'Testing...' : 'Test'}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onEdit(c);
                        }}
                        className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-200 transition-colors"
                        style={{ cursor: 'pointer' }}
                      >
                        Edit
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          confirmDelete(c.id);
                        }}
                        className="text-xs px-2 py-1 rounded bg-red-700 hover:bg-red-600 text-white transition-colors"
                        style={{ cursor: 'pointer' }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
                {connections.length === 0 && (
                  <div className="text-xs text-gray-500">
                    No connections yet.
                  </div>
                )}
              </div>
              <div className="mt-3">
                <button
                  className="text-xs text-gray-400 underline cursor-pointer"
                  onClick={onRefresh}
                >
                  Refresh list
                </button>
              </div>
            </div>

            <ConfirmationModal
              open={confirmOpen}
              title="Delete connection"
              message="This will permanently delete the connection. Continue?"
              onConfirm={handleConfirm}
              onCancel={handleCancel}
            />
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default ConnectionsSidebar;
