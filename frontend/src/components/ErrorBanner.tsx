import React from "react";

type Props = {
  message: string | null;
  onClose?: () => void;
};

const ErrorBanner: React.FC<Props> = ({ message, onClose }) => {
  if (!message) return null;

  return (
    <div className="error-banner">
      <span>{message}</span>
      {onClose && (
        <button className="error-close" onClick={onClose}>
          ×
        </button>
      )}
    </div>
  );
};

export default ErrorBanner;
