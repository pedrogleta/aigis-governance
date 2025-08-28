import React, { useEffect, useRef, useState } from 'react';
// icons not needed here
import { cn } from '../lib/utils';
import type {
  UserConnection,
  UserConnectionCreate,
  CsvUploadPreview,
} from '../services/api';
import { apiService } from '../services/api';
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
  const [showFormModal, setShowFormModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importStep, setImportStep] = useState<'upload' | 'types'>('upload');
  const [csvPreview, setCsvPreview] = useState<CsvUploadPreview | null>(null);
  const [columnTypes, setColumnTypes] = useState<Record<string, string>>({});
  const [importBusy, setImportBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

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
    if (open || showFormModal) firstInputRef.current?.focus();
  }, [open, showFormModal]);

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

            {/* Connections list shown first */}
            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-2">
                Your connections
              </h3>
              <div className="space-y-2 mb-6">
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
                        className="h-4 w-4 mr-3 accent-green-500 bg-gray-800 border-gray-700 rounded focus:ring-2 focus:ring-green-500"
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
                          setShowFormModal(true);
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
            </div>

            <div className="mt-3 flex items-center justify-between">
              <button
                className="text-xs text-gray-400 underline cursor-pointer"
                onClick={onRefresh}
              >
                Refresh list
              </button>
              <div className="flex items-center gap-2">
                <button
                  className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded text-sm cursor-pointer"
                  onClick={() => setShowImportModal(true)}
                >
                  Import CSV
                </button>
                <button
                  className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm cursor-pointer"
                  onClick={() => {
                    setEditingId(null);
                    setFormState({ name: '', db_type: 'postgres' });
                    setShowFormModal(true);
                  }}
                >
                  Create connection
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

            {/* Form modal for create / edit */}
            <AnimatePresence>
              {showFormModal && (
                <div className="fixed inset-0 z-30">
                  <motion.div
                    className="absolute inset-0 bg-black/50"
                    onClick={() => setShowFormModal(false)}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.6 }}
                    exit={{ opacity: 0 }}
                  />
                  <motion.div
                    className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-gray-900 border border-gray-800 rounded p-6 z-40"
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.95, opacity: 0 }}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">
                        {editingId ? 'Edit connection' : 'Create connection'}
                      </h3>
                      <button
                        onClick={() => setShowFormModal(false)}
                        className="text-gray-400 hover:text-gray-200 cursor-pointer"
                      >
                        Close
                      </button>
                    </div>

                    <div className="space-y-2">
                      <label className="block text-sm text-gray-300">
                        Name
                      </label>
                      <input
                        ref={firstInputRef}
                        className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                        value={formState.name || ''}
                        onChange={(e) =>
                          setFormState({ ...formState, name: e.target.value })
                        }
                        placeholder="My Postgres"
                      />
                      <label className="block text-sm text-gray-300 mt-3">
                        Type
                      </label>
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
                              setFormState({
                                ...formState,
                                host: e.target.value,
                              })
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
                              setFormState({
                                ...formState,
                                host: e.target.value,
                              })
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
                              setFormState({
                                ...formState,
                                username: e.target.value,
                              })
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
                              setFormState({
                                ...formState,
                                password: e.target.value,
                              })
                            }
                            placeholder={
                              editingId
                                ? 'Leave blank to keep current'
                                : 'Password'
                            }
                          />
                        </>
                      )}

                      <div className="flex items-center space-x-2 mt-4">
                        <button
                          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded cursor-pointer"
                          onClick={() => {
                            onSave();
                            setShowFormModal(false);
                            setEditingId(null);
                          }}
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
                        <button
                          className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded cursor-pointer"
                          onClick={() => setShowFormModal(false)}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </motion.div>
                </div>
              )}
            </AnimatePresence>

            {/* Import CSV modal */}
            <AnimatePresence>
              {showImportModal && (
                <div className="fixed inset-0 z-30">
                  <motion.div
                    className="absolute inset-0 bg-black/50"
                    onClick={() => setShowImportModal(false)}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.6 }}
                    exit={{ opacity: 0 }}
                  />
                  <motion.div
                    className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl bg-gray-900 border border-gray-800 rounded p-6 z-40 max-h-[85vh] overflow-y-auto"
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.95, opacity: 0 }}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">
                        Import CSV
                      </h3>
                      <button
                        onClick={() => setShowImportModal(false)}
                        className="text-gray-400 hover:text-gray-200 cursor-pointer"
                      >
                        Close
                      </button>
                    </div>

                    {importStep === 'upload' && (
                      <div className="space-y-4">
                        <p className="text-sm text-gray-300">
                          Upload a CSV file to import into your personal
                          Postgres schema.
                        </p>
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept=".csv,text/csv"
                          className="w-full text-sm text-gray-200"
                          onChange={async (e) => {
                            const file = e.target.files?.[0];
                            if (!file) return;
                            setImportBusy(true);
                            try {
                              const preview = await apiService.uploadCsv(file);
                              setCsvPreview(preview);
                              // init column types to text by default
                              const init: Record<string, string> = {};
                              for (const h of preview.headers) init[h] = 'text';
                              setColumnTypes(init);
                              setImportStep('types');
                            } catch (err) {
                              console.error(err);
                              alert((err as Error).message);
                            } finally {
                              setImportBusy(false);
                            }
                          }}
                        />
                        {importBusy && (
                          <div className="text-xs text-gray-400">
                            Uploading…
                          </div>
                        )}
                      </div>
                    )}

                    {importStep === 'types' && csvPreview && (
                      <div className="space-y-4">
                        <div>
                          <div className="text-sm text-gray-300">
                            File:{' '}
                            <span className="text-gray-200">
                              {csvPreview.filename}
                            </span>
                          </div>
                          <div className="text-xs text-gray-400">
                            Detected columns: {csvPreview.headers.length}
                          </div>
                        </div>
                        <div className="overflow-auto border border-gray-800 rounded">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="bg-gray-800">
                                <th className="text-left p-2 text-gray-200">
                                  Column
                                </th>
                                <th className="text-left p-2 text-gray-200">
                                  Type
                                </th>
                                <th className="text-left p-2 text-gray-200">
                                  Sample
                                </th>
                              </tr>
                            </thead>
                            <tbody>
                              {csvPreview.headers.map((h, idx) => (
                                <tr
                                  key={h}
                                  className="border-t border-gray-800"
                                >
                                  <td className="p-2 text-gray-100">{h}</td>
                                  <td className="p-2">
                                    <select
                                      className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-100"
                                      value={columnTypes[h] || 'text'}
                                      onChange={(e) =>
                                        setColumnTypes({
                                          ...columnTypes,
                                          [h]: e.target.value,
                                        })
                                      }
                                    >
                                      <option value="text">Text</option>
                                      <option value="integer">Integer</option>
                                      <option value="float">Float</option>
                                      <option value="boolean">Boolean</option>
                                      <option value="date">Date</option>
                                      <option value="timestamp">
                                        Timestamp
                                      </option>
                                    </select>
                                  </td>
                                  <td className="p-2 text-gray-300">
                                    <div className="flex flex-wrap gap-2">
                                      {csvPreview.sample.map((r, rIdx) => (
                                        <span
                                          key={rIdx}
                                          className="px-2 py-0.5 bg-gray-800 rounded text-xs text-gray-300"
                                        >
                                          {r[idx] ?? ''}
                                        </span>
                                      ))}
                                    </div>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm cursor-pointer disabled:opacity-50"
                            disabled={importBusy}
                            onClick={async () => {
                              if (!csvPreview) return;
                              setImportBusy(true);
                              try {
                                const conn = await apiService.finishImportCsv(
                                  csvPreview.filename,
                                  csvPreview.raw,
                                  columnTypes,
                                );
                                // refresh and select the newly created custom connection
                                await onRefresh();
                                onSelect(conn);
                                setShowImportModal(false);
                                // reset state
                                setImportStep('upload');
                                setCsvPreview(null);
                                setColumnTypes({});
                              } catch (err) {
                                console.error(err);
                                alert((err as Error).message);
                              } finally {
                                setImportBusy(false);
                              }
                            }}
                          >
                            {importBusy ? 'Importing…' : 'Finish import'}
                          </button>
                          <button
                            className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm cursor-pointer"
                            onClick={() => {
                              setImportStep('upload');
                              setCsvPreview(null);
                              setColumnTypes({});
                            }}
                          >
                            Back
                          </button>
                        </div>
                      </div>
                    )}
                  </motion.div>
                </div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default ConnectionsSidebar;
