import React from 'react';

interface Props {
  open: boolean;
  title?: string;
  message?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmationModal: React.FC<Props> = ({
  open,
  title = 'Confirm',
  message = 'Are you sure?',
  onConfirm,
  onCancel,
}) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onCancel}
        style={{ cursor: 'pointer' }}
      />
      <div className="relative bg-gray-900 border border-gray-800 rounded-lg p-6 w-full max-w-md z-40">
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
        <div className="text-sm text-gray-300 mb-4">{message}</div>
        <div className="flex justify-end space-x-2">
          <button
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded cursor-pointer"
            onClick={onCancel}
          >
            Cancel
          </button>
          <button
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded cursor-pointer"
            onClick={onConfirm}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;
