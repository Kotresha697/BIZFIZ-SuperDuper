import * as React from 'react';

import './index.css'

export default function NavBar({ title, authed, onLogout }) {
  return (
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container">

        <div class="navbar-brand d-flex" style={{width:'100%'}} >
          <img src="https://i.ibb.co/6vYxk8n/logo.png" class="h-8" style={{width:'40px'}} alt="..."></img>
          <span className="mx-1 " style={{paddingTop:'5px'}}>BIZFIZ</span>
          <div className=" nav-title  mx-auto">  {title}</div>
        </div>

        {authed ? (
          <button
            type="button"
            onClick={onLogout}
            style={{
              flexShrink: 0,
              border: 0,
              borderRadius: '8px',
              padding: '8px 14px',
              color: '#fff',
              background: '#4f46e5',
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            Log out
          </button>
        ) : null}

      </div>
    </nav>
  )
}

