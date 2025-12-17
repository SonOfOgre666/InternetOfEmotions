"use client";

import { useEffect, useState } from "react";

export default function ClientBody({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mounted, setMounted] = useState(false);

  // Wait for client-side hydration to complete before rendering
  useEffect(() => {
    setMounted(true);
    
    // Clean up any browser extension modifications
    const cleanExtensionAttributes = () => {
      // Remove DarkReader and other extension attributes
      document.querySelectorAll('[data-darkreader-inline-stroke]').forEach(el => {
        el.removeAttribute('data-darkreader-inline-stroke');
      });
      document.querySelectorAll('[data-darkreader-inline-fill]').forEach(el => {
        el.removeAttribute('data-darkreader-inline-fill');
      });
    };
    
    cleanExtensionAttributes();
    
    // Set up observer to clean attributes as they're added
    const observer = new MutationObserver(cleanExtensionAttributes);
    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ['data-darkreader-inline-stroke', 'data-darkreader-inline-fill'],
      subtree: true
    });
    
    return () => observer.disconnect();
  }, []);

  // Render null on server and until mounted on client to avoid hydration mismatch
  if (!mounted) {
    return null;
  }

  return <>{children}</>;
}