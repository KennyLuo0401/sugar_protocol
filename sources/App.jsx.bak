// frontend/src/App.jsx
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { ForceGraph3D } from 'react-force-graph';
import { SuiClient, getFullnodeUrl } from '@mysten/sui.js/client';

// 🟢 這是根據你的 doctor_raw.py 驗證過的正確 ID
const PACKAGE_ID = "0x3a89bbef10712247d2ef6bdf70ea9ea3c500182d060c6d507a0cfaf467cead75";
const client = new SuiClient({ url: getFullnodeUrl('testnet') });

const SugarMap = () => {
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [logs, setLogs] = useState(["⏳ 系統初始化..."]); // 螢幕日誌

  // 輔助函數：增加日誌到螢幕
  const addLog = (msg) => setLogs(prev => [msg, ...prev].slice(0, 10));

  useEffect(() => {
    const fetchData = async () => {
      try {
        addLog(`🚀 開始連接 Sui Testnet...`);
        addLog(`📦 目標合約: ${PACKAGE_ID.slice(0, 8)}...`);

        // 1. 使用 queryEvents (跟 doctor_raw.py 一樣的方法)
        const eventFilter = { MoveEventType: `${PACKAGE_ID}::core::GrainMinted` };
        
        const events = await client.queryEvents({
          query: eventFilter,
          limit: 50,
          order: "descending"
        });

        addLog(`📡 掃描到 ${events.data.length} 筆事件`);

        if (events.data.length === 0) {
          addLog("❌ 嚴重警告：找不到任何事件！");
          return;
        }

        // 2. 提取 ID
        const objectIds = events.data.map(e => e.parsedJson.grain_id);
        addLog(`🔍 準備讀取 ${objectIds.length} 個物件...`);

        // 3. 批量讀取內容
        const objects = await client.multiGetObjects({
          ids: objectIds,
          options: { showContent: true }
        });

        const rawNodes = [];
        const rawLinks = [];
        let rootCount = 0;
        let childCount = 0;

        objects.forEach(item => {
          if (item.data && item.data.content) {
            const fields = item.data.content.fields;
            const nodeId = item.data.objectId;

            // 統計數量
            if (fields.bond_type === 0) rootCount++;
            else childCount++;

            // 建立節點
            rawNodes.push({
              id: nodeId,
              content: fields.content,
              bond_type: fields.bond_type,
              color: fields.bond_type === 3 ? '#ff4d4d' : (fields.bond_type === 0 ? '#ffa500' : '#00ff80')
            });

            // 建立連線 (支援 parents 或 parent_ids)
            const parents = fields.parents || fields.parent_ids || [];
            if (Array.isArray(parents)) {
              parents.forEach(parentId => {
                rawLinks.push({
                  source: parentId,
                  target: nodeId,
                  color: fields.bond_type === 3 ? '#ff4d4d' : '#ffffff'
                });
              });
            }
          }
        });

        addLog(`✅ 解析完成: ${rootCount} 核心, ${childCount} 子節點`);
        setNodes(rawNodes);
        setLinks(rawLinks);

      } catch (error) {
        console.error(error);
        addLog(`❌ 發生錯誤: ${error.message}`);
      }
    };
    
    fetchData(); 
  }, []);

  const graphData = useMemo(() => ({ nodes, links }), [nodes, links]);

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#000', position: 'relative' }}>
      
      {/* 🖥️ 螢幕除錯面板 (這樣你就知道發生什麼事了) */}
      <div style={{
        position: 'absolute', top: 20, left: 20, zIndex: 999,
        background: 'rgba(0,0,0,0.7)', padding: '15px', borderRadius: '8px',
        color: '#0f0', fontFamily: 'monospace', maxWidth: '400px', pointerEvents: 'none'
      }}>
        <h3 style={{ margin: '0 0 10px 0', borderBottom: '1px solid #333' }}>🩺 Sugar System Log</h3>
        {logs.map((log, i) => (
          <div key={i} style={{ fontSize: '12px', marginBottom: '4px' }}>{log}</div>
        ))}
      </div>

      <ForceGraph3D
        graphData={graphData}
        nodeLabel="content"
        nodeColor="color"
        linkColor="color"
        linkWidth={1.5}
        nodeRelSize={6}
        linkOpacity={0.6}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.005}
      />
    </div>
  );
};

export default SugarMap;