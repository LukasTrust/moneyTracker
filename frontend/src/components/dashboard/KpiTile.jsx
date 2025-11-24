import React, { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';

/**
 * KpiTile - small tile showing an animated numeric KPI
 * Props:
 * - label: string
 * - value: number
 * - prefix: string
 * - suffix: string
 * - decimals: number
 * - className: additional classes
 */
export default function KpiTile({ label, value = 0, prefix = '', suffix = '', decimals = 0, className = '', icon = null, accent = 'gray' }) {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef(null);
  const startRef = useRef(null);
  const fromRef = useRef(0);

  useEffect(() => {
    // animate from current displayed value to new value in ~700ms
    const duration = 700;
    const start = performance.now();
    startRef.current = start;
    fromRef.current = display;

    const step = (now) => {
      const t = Math.min(1, (now - start) / duration);
      // easeOutQuad
      const eased = 1 - (1 - t) * (1 - t);
      const current = fromRef.current + (value - fromRef.current) * eased;
      setDisplay(current);
      if (t < 1) {
        rafRef.current = requestAnimationFrame(step);
      }
    };

    cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(step);

    return () => cancelAnimationFrame(rafRef.current);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const formatted = Number(display).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });

  // Accent color mapping (Tailwind classes)
  const colorMap = {
    green: {
      bg: 'bg-green-50',
      text: 'text-green-700',
      ring: 'ring-green-100'
    },
    red: {
      bg: 'bg-red-50',
      text: 'text-red-700',
      ring: 'ring-red-100'
    },
    blue: {
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      ring: 'ring-blue-100'
    },
    purple: {
      bg: 'bg-purple-50',
      text: 'text-purple-700',
      ring: 'ring-purple-100'
    },
    yellow: {
      bg: 'bg-yellow-50',
      text: 'text-yellow-700',
      ring: 'ring-yellow-100'
    },
    gray: {
      bg: 'bg-gray-50',
      text: 'text-gray-700',
      ring: 'ring-gray-100'
    }
  };

  const accentClasses = colorMap[accent] || colorMap.gray;

  return (
    <div className={`bg-white rounded-lg shadow p-4 flex flex-col ${className}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`flex items-center justify-center h-9 w-9 rounded-full ${accentClasses.bg} ${accentClasses.ring} ring-1`}> 
            <span className={`text-lg ${accentClasses.text}`}>{icon || '📊'}</span>
          </div>
          <div className="text-xs text-gray-500">{label}</div>
        </div>
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        {prefix && <div className="text-sm text-gray-400">{prefix}</div>}
        <div className="text-2xl font-semibold text-gray-900">{formatted}</div>
        {suffix && <div className="text-sm text-gray-500">{suffix}</div>}
      </div>
    </div>
  );
}

KpiTile.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.number,
  prefix: PropTypes.string,
  suffix: PropTypes.string,
  decimals: PropTypes.number,
  className: PropTypes.string
};
