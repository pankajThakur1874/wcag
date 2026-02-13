/**
 * Pagination Component
 *
 * Reusable pagination UI with page numbers and Load More option.
 */

import React from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
  loading?: boolean;
}

export function Pagination({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  loading = false
}: PaginationProps) {
  if (totalPages <= 1) return null;

  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const showEllipsis = totalPages > 7;

    if (!showEllipsis) {
      // Show all pages if 7 or less
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);

      if (currentPage > 3) {
        pages.push('...');
      }

      // Show pages around current page
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (currentPage < totalPages - 2) {
        pages.push('...');
      }

      // Always show last page
      pages.push(totalPages);
    }

    return pages;
  };

  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: '1.5rem',
        padding: '1rem',
        borderTop: '1px solid var(--border-light)',
        flexWrap: 'wrap',
        gap: '1rem'
      }}
    >
      {/* Items count */}
      <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
        Showing <strong>{startItem}</strong> to <strong>{endItem}</strong> of{' '}
        <strong>{totalItems}</strong> items
      </div>

      {/* Page numbers */}
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        {/* Previous button */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1 || loading}
          style={{
            padding: '0.5rem 0.75rem',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-md)',
            background: 'white',
            cursor: currentPage === 1 || loading ? 'not-allowed' : 'pointer',
            fontFamily: 'inherit',
            fontSize: '0.9rem',
            opacity: currentPage === 1 || loading ? 0.5 : 1
          }}
        >
          ← Previous
        </button>

        {/* Page numbers */}
        {getPageNumbers().map((page, index) => {
          if (page === '...') {
            return (
              <span
                key={`ellipsis-${index}`}
                style={{
                  padding: '0.5rem 0.75rem',
                  color: 'var(--text-secondary)'
                }}
              >
                ...
              </span>
            );
          }

          const pageNum = page as number;
          const isActive = pageNum === currentPage;

          return (
            <button
              key={pageNum}
              onClick={() => onPageChange(pageNum)}
              disabled={loading}
              style={{
                padding: '0.5rem 0.75rem',
                border: isActive ? '2px solid var(--primary-start)' : '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)',
                background: isActive ? 'rgba(79, 70, 229, 0.1)' : 'white',
                color: isActive ? 'var(--primary-start)' : 'var(--text-main)',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontFamily: 'inherit',
                fontSize: '0.9rem',
                fontWeight: isActive ? 600 : 400,
                minWidth: '40px'
              }}
            >
              {pageNum}
            </button>
          );
        })}

        {/* Next button */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages || loading}
          style={{
            padding: '0.5rem 0.75rem',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-md)',
            background: 'white',
            cursor: currentPage === totalPages || loading ? 'not-allowed' : 'pointer',
            fontFamily: 'inherit',
            fontSize: '0.9rem',
            opacity: currentPage === totalPages || loading ? 0.5 : 1
          }}
        >
          Next →
        </button>
      </div>
    </div>
  );
}

// Alternative: Load More button style
interface LoadMoreProps {
  hasMore: boolean;
  loading: boolean;
  onLoadMore: () => void;
  itemsLoaded: number;
  totalItems: number;
}

export function LoadMore({ hasMore, loading, onLoadMore, itemsLoaded, totalItems }: LoadMoreProps) {
  if (!hasMore) return null;

  return (
    <div style={{ textAlign: 'center', marginTop: '2rem' }}>
      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
        Showing {itemsLoaded} of {totalItems} items
      </p>
      <button
        onClick={onLoadMore}
        disabled={loading}
        className="btn-gradient"
        style={{
          padding: '0.75rem 2rem',
          opacity: loading ? 0.6 : 1,
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? 'Loading...' : 'Load More'}
      </button>
    </div>
  );
}
