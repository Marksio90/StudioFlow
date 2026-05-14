import Link from 'next/link';
import { ReactNode } from 'react';

export default function Layout({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="container">
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 20 }}>
        <h1 style={{ margin: 0 }}>{title}</h1>
        <div className="row">
          <Link href="/">Dashboard</Link>
          <Link href="/projects">Projects</Link>
          <Link href="/projects/new">Create</Link>
        </div>
      </div>
      {children}
    </div>
  );
}
