// frontend/src/App.jsx
import React, { useState, useEffect, useMemo } from 'react';
import ForceGraph3D from 'react-force-graph-3d'; 
import { SuiClient, getFullnodeUrl } from '@mysten/sui.js/client';

// 你的合約 Package ID
const PACKAGE_ID = "0x3a89bbef10712247d2ef6bdf70ea9ea3c500182d060c6d507a0cfaf467cead75";
const client = new SuiClient({ url: getFullnodeUrl('testnet') });

const SugarMap = () => {
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [logs, setLogs] = useState(["⏳ 系統初始化..."]);

  // 增加日誌 (保留最新的 10 筆)
  const addLog = (msg) => setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 10));

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 1. 用 cursor-based 分頁抓取所有事件
        const allEvents = [];
        let cursor = null;
        let hasNext = true;

        while (hasNext) {
          const page = await client.queryEvents({
            query: { MoveEventType: `${PACKAGE_ID}::core::GrainMinted` },
            limit: 50,
            order: "descending",
            ...(cursor ? { cursor } : {}),
          });
          allEvents.push(...page.data);
          hasNext = page.hasNextPage;
          cursor = page.nextCursor;
        }

        if (allEvents.length === 0) return;

        // 2. 提取物件 ID
        const objectIds = allEvents.map(e => e.parsedJson.grain_id);
        
        // 3. 批量讀取內容 (每批最多 50 個，避免 API 限制)
        const objects = [];
        for (let i = 0; i < objectIds.length; i += 50) {
          const batch = objectIds.slice(i, i + 50);
          const result = await client.multiGetObjects({
            ids: batch,
            options: { showContent: true }
          });
          objects.push(...result);
        }

        const rawNodes = [];
        const rawLinks = [];
        const validNodeIds = new Set();

        // 4. 建立點名簿 (確認哪些 ID 是真的抓到了)
        objects.forEach(item => {
            if (item.data) validNodeIds.add(item.data.objectId);
        });

        // 5. 解析資料
        objects.forEach(item => {
          if (item.data && item.data.content) {
            const fields = item.data.content.fields;
            const nodeId = item.data.objectId;

            // 建立節點
            rawNodes.push({
              id: nodeId,
              content: fields.content,
              bond_type: fields.bond_type
            });

            // 建立連線
            const parents = fields.parents || fields.parent_ids || [];
            if (Array.isArray(parents)) {
              parents.forEach(parentId => {
                // 🛡️ 防崩潰檢查：只有當爸爸也在這次抓到的清單裡，才畫線
                if (validNodeIds.has(parentId)) {
                  rawLinks.push({
                    source: parentId,
                    target: nodeId
                  });
                }
              });
            }
          }
        });

        // 更新 React 狀態
        setNodes(rawNodes);
        setLinks(rawLinks);
        addLog(`🔄 更新完成: ${rawNodes.length} 節點`);

      } catch (error) {
        console.error(error);
        addLog(`❌ 更新失敗: ${error.message}`);
      }
    };
    
    // 🚀 1. 網頁剛打開時，先執行一次
    fetchData(); 

    // ⏰ 2. 設定定時器：每 5000 毫秒 (5秒) 自動執行一次
    const intervalId = setInterval(() => {
        fetchData();
    }, 5000);

    // 🧹 3. 清理函數：當使用者關閉網頁時，停止定時器 (避免記憶體洩漏)
    return () => clearInterval(intervalId);

  }, []);

  const graphData = useMemo(() => ({ nodes, links }), [nodes, links]);

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#000', position: 'relative' }}>
      
      {/* 綠色日誌面板 */}
      <div style={{
        position: 'absolute', top: 20, left: 20, zIndex: 999,
        background: 'rgba(0,0,0,0.8)', padding: '15px', borderRadius: '8px',
        color: '#0f0', fontFamily: 'monospace', pointerEvents: 'none',
        minWidth: '250px'
      }}>
        <h3 style={{ margin: '0 0 10px 0', borderBottom: '1px solid #333' }}>📡 Live Monitor</h3>
        {logs.map((log, i) => <div key={i} style={{fontSize: '12px', marginBottom: '4px'}}>{log}</div>)}
      </div>

      <ForceGraph3D
        graphData={graphData}
        nodeLabel="content"
        nodeColor={node => {
          if (node.bond_type === 0) return '#ffa500'; // 橘色核心
          if (node.bond_type === 3) return '#ff4d4d'; // 紅色衝突
          return '#00ff80'; // 綠色支持
        }}
        linkColor={link => {
          const target = nodes.find(n => n.id === link.target);
          return target?.bond_type === 3 ? '#ff4d4d' : '#ffffff';
        }}
        linkWidth={1.5}
        nodeRelSize={6}
        linkOpacity={0.6}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.005}
        
        // 點擊跳轉 Suiscan
        onNodeClick={node => {
            window.open(`https://suiscan.xyz/testnet/object/${node.id}`, '_blank');
        }}
        cursor="pointer"
      />
    </div>
  );
};

export default SugarMap;