import React, { useEffect, useState, useRef } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import { SuiClient, getFullnodeUrl } from '@mysten/sui.js/client';

const PACKAGE_ID = "0x3a89bbef10712247d2ef6bdf70ea9ea3c500182d060c6d507a0cfaf467cead75"; 
const MODULE_NAME = "core";
const EVENT_NAME = "GrainMinted";

const client = new SuiClient({ url: getFullnodeUrl('testnet') });

// 🛠️ 小工具：把大陣列切成小塊 (Chunking)
// 因為 Sui RPC 規定一次 multiGetObjects 最多只能抓 50 個
function chunkArray(array, size) {
  const result = [];
  for (let i = 0; i < array.length; i += size) {
    result.push(array.slice(i, i + size));
  }
  return result;
}

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [status, setStatus] = useState("初始化中...");
  const hasLoggedDebug = useRef(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setStatus("1. 正在搜尋鏈上事件 (擴大範圍)...");
        
        // 🔥 修改 1: 將讀取範圍擴大到 300，確保能挖到被淹沒的星系
        const events = await client.queryEvents({
          query: { MoveEventType: `${PACKAGE_ID}::${MODULE_NAME}::${EVENT_NAME}` },
          limit: 300, 
          order: "descending"
        });

        const initialIds = Array.from(new Set(events.data.map(e => e.parsedJson.grain_id)));
        if (initialIds.length === 0) {
            setStatus("⚠️ 鏈上沒有任何數據");
            return;
        }

        setStatus(`2. 正在分批抓取 ${initialIds.length} 顆晶體...`);

        // 🔥 修改 2: 分批讀取 (Chunking Logic)
        // 避免 "Too many IDs" 錯誤
        const chunks = chunkArray(initialIds, 50);
        let objects = [];
        
        for (const chunk of chunks) {
            const res = await client.multiGetObjects({
                ids: chunk,
                options: { showContent: true }
            });
            objects = [...objects, ...res];
        }

        // ====================================================
        // 🕵️ 暴力偵錯區 (這次加上來源過濾)
        // ====================================================
        if (!hasLoggedDebug.current) {
            console.log("%c============== 🕵️ 數據來源檢查 ==============", "color: cyan; font-size: 14px");
            const abmediaCount = objects.filter(o => o.data?.content?.fields?.source_url?.includes("abmedia")).length;
            const techCount = objects.filter(o => o.data?.content?.fields?.source_url?.includes("techcrunch")).length;
            
            console.log(`📊 統計數據 (前 ${objects.length} 筆):`);
            console.log(`   - 🟣 Abmedia (應該要有連線): ${abmediaCount} 顆`);
            console.log(`   - ⚪ TechCrunch (孤兒): ${techCount} 顆`);
            
            if (abmediaCount === 0) {
                console.warn("⚠️ 警告：目前載入範圍內找不到 Abmedia 的資料！請跑 batch_runner.py 或再加大 limit。");
            }
            console.log("%c============================================", "color: cyan");
            hasLoggedDebug.current = true;
        }

        // ====================================================
        // 🚀 補全父母 (Parent Hydration)
        // ====================================================
        let allObjects = [...objects];
        const currentIdSet = new Set(initialIds); 
        const missingParentIds = new Set();       

        objects.forEach(obj => {
            if (obj.data && obj.data.content) {
                const fields = obj.data.content.fields;
                const parents = fields.parents || fields.parent_ids || []; 
                parents.forEach(pId => {
                    if (!currentIdSet.has(pId)) missingParentIds.add(pId);
                });
            }
        });

        if (missingParentIds.size > 0) {
            setStatus(`3. 正在補全 ${missingParentIds.size} 個父節點...`);
            const missingArray = Array.from(missingParentIds);
            const parentChunks = chunkArray(missingArray, 50); // 父母也要分批抓
            
            for (const chunk of parentChunks) {
                const res = await client.multiGetObjects({
                    ids: chunk,
                    options: { showContent: true }
                });
                allObjects = [...allObjects, ...res];
            }
        }

        // ====================================================
        // Step 3: 建構圖表
        // ====================================================
        const nodes = [];
        const links = [];
        const validNodeIds = new Set(); 

        // Node 建構
        allObjects.forEach((obj) => {
          if (obj.data && obj.data.content) {
            const fields = obj.data.content.fields;
            const myId = obj.data.objectId;

            if (validNodeIds.has(myId)) return;
            validNodeIds.add(myId);

            const parents = fields.parents || fields.parent_ids || [];
            
            // 顏色邏輯
            let color = "#4da6ff"; // Default
            if (fields.source_url && fields.source_url.includes("abmedia")) {
                // 給 Abmedia 的球一點特殊的亮度，方便辨識
                if (fields.bond_type == 1) color = "#00ff80"; 
                if (fields.bond_type == 3) color = "#ff4d4d"; 
                if (fields.bond_type == 0 && parents.length === 0) color = "#ffaa00";
            } else {
                // TechCrunch 的孤兒給灰色，讓它們不要太搶眼
                color = "#888888";
            }

            nodes.push({
              id: myId,
              name: fields.content,
              val: 10,
              color: color
            });
          }
        });

        // Link 建構
        allObjects.forEach((obj) => {
            if (obj.data && obj.data.content) {
                const fields = obj.data.content.fields;
                const myId = obj.data.objectId;
                const parents = fields.parents || fields.parent_ids || [];

                parents.forEach(parentId => {
                    if (validNodeIds.has(parentId)) {
                        links.push({ source: parentId, target: myId });
                    }
                });
            }
        });

        setStatus(`✅ 完成！節點: ${nodes.length} | 連線: ${links.length}`);
        setGraphData({ nodes, links });

      } catch (error) {
        console.error("讀取失敗:", error);
        setStatus("❌ 發生錯誤 (請看 Console)");
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000); // 改成 10 秒刷一次，避免 Request 太多
    return () => clearInterval(interval);

  }, []);

  return (
    <div style={{ margin: 0, padding: 0, width: "100vw", height: "100vh", background: "#000" }}>
        <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 99, color: 'white', fontFamily: 'monospace', background: 'rgba(0,0,0,0.7)', padding: '10px', borderRadius: '8px' }}>
            <h1 style={{ margin: 0, fontSize: '24px' }}>🍬 Sugar Map (Testnet)</h1>
            <p style={{ color: '#00ff00', margin: '5px 0' }}>{status}</p>
            <div style={{ marginTop: 10, fontSize: '12px' }}>
                <span style={{color:'#ffaa00'}}>● ROOT</span>&nbsp;
                <span style={{color:'#00ff80'}}>● ABMEDIA</span>&nbsp;
                <span style={{color:'#888888'}}>● OTHERS</span>
            </div>
        </div>

        {graphData.nodes.length > 0 && (
            <ForceGraph3D
                graphData={graphData}
                nodeLabel="name"
                nodeColor="color"
                nodeRelSize={6}
                linkColor={() => "#ffffff"}
                linkWidth={2}
                linkOpacity={1}
                backgroundColor="#050505"
                onNodeClick={node => window.open(`https://suiscan.xyz/testnet/object/${node.id}`, '_blank')}
            />
        )}
    </div>
  );
}

export default App;