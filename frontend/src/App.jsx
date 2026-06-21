import { useState } from 'react';

function App() {
  const [currentStep, setCurrentStep] = useState(0);
  const [blogUrl, setBlogUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedImages, setSelectedImages] = useState([]);
  
  const [projectData, setProjectData] = useState({
    title: '',
    summary: '',
    keywords: [],
    script: { hook: '', body: '', ending: '' },
    images: [], 
    scenes: [], // 💡 백엔드 실시간 장면 데이터 스토어
    selectedVoice: 'alloy',
    selectedTemplate: 'dark',
    audioUrl: '',
    videoUrl: ''
  });

  const stepsList = [
    { id: 1, name: '기획하기' },
    { id: 2, name: '대본 선택' },
    { id: 3, name: '주요 이미지 선택' },
    { id: 4, name: '장면별 이미지' },
    { id: 5, name: '제목 생성' },
    { id: 6, name: '목소리 선택' },
    { id: 7, name: '템플릿 매칭' }
  ];

  const handleStartAnalysis = async () => {
    if (!blogUrl) {
      alert('네이버 블로그 URL을 입력해주세요.');
      return;
    }
    setIsAnalyzing(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: blogUrl }),
      });
      if (!response.ok) throw new Error('백엔드 서버 통신 실패');
      const data = await response.json();
      
      setProjectData(prev => ({
        ...prev,
        title: data.title,
        images: data.images || [], 
        script: data.script,
        scenes: data.scenes || [] // 💡 백엔드가 쪼개준 실제 씬 리스트 저장
      }));
      
      setSelectedImages(data.images || []);
      setCurrentStep(3); 
    } catch (error) {
      console.error(error);
      alert('분석 오류가 발생했습니다.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleToggleImage = (imgUrl) => {
    if (selectedImages.includes(imgUrl)) {
      setSelectedImages(selectedImages.filter(url => url !== imgUrl));
    } else {
      setSelectedImages([...selectedImages, imgUrl]);
    }
  };

  const handleLocalImageUpload = (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    const newImageUrls = files.map(file => URL.createObjectURL(file));
    setProjectData(prev => ({ ...prev, images: [...prev.images, ...newImageUrls] }));
    setSelectedImages(prev => [...prev, ...newImageUrls]);
  };

  // 💡 [슈퍼쇼츠 핵심: 콘티 실시간 편집 로직] 사용자가 텍스트 박스를 고치면 상태창에 즉시 반영
  const handleSceneTextChange = (sceneId, field, newValue) => {
    setProjectData(prev => ({
      ...prev,
      scenes: prev.scenes.map(scene => 
        scene.id === sceneId ? { ...scene, [field]: newValue } : scene
      )
    }));
  };

  const handleVoiceGeneration = async () => {
    // 사용자가 에디터 그리드에서 수정한 실시간 텍스트들을 전부 긁어모아 오디오 인코더로 전송합니다.
    const combinedScript = projectData.scenes.map(s => s.script).join(' ');
    try {
      const response = await fetch('http://127.0.0.1:8000/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: combinedScript, voice: projectData.selectedVoice })
      });
      if (!response.ok) throw new Error('TTS 에러');
      const data = await response.json();
      setProjectData(prev => ({ ...prev, audioUrl: data.audio_url }));
      setCurrentStep(7);
    } catch (error) {
      console.error(error);
      alert('음성 생성에 실패했습니다.');
    }
  };

  const handleFinalVideoGeneration = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/video', { method: 'POST' });
      if (!response.ok) throw new Error('비디오 에러');
      const data = await response.json();
      setProjectData(prev => ({ ...prev, videoUrl: data.video_url }));
      setCurrentStep(8);
    } catch (error) {
      console.error(error);
      alert('영상 제작 중 오류가 발생했습니다.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans antialiased">
      
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col p-6 shrink-0">
        <div className="flex items-center gap-2 mb-8 px-2">
          <span className="w-3 h-3 rounded-full bg-blue-500 animate-pulse"></span>
          <span className="font-black tracking-wider text-lg">SuperShorts AI</span>
        </div>
        <nav className="flex flex-col gap-1 flex-1">
          {stepsList.map((st) => {
            const isCurrent = currentStep === st.id;
            const isPast = currentStep > st.id;
            return (
              <div
                key={st.id}
                className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-bold transition-all ${
                  isCurrent ? 'bg-blue-600 text-white shadow-lg' : isPast ? 'text-blue-400 bg-blue-500/5' : 'text-slate-500'
                }`}
              >
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs border ${
                  isCurrent ? 'border-white bg-white text-blue-600' : isPast ? 'border-blue-400 bg-blue-500/10' : 'border-slate-700'
                }`}>
                  {st.id}
                </span>
                {st.name}
              </div>
            );
          })}
        </nav>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-slate-900 flex items-center justify-between px-8 bg-slate-900/40 backdrop-blur-md">
          <span className="text-sm font-bold text-slate-400">대시보드 &gt; 프로젝트 생성</span>
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-sm">USER</div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto max-w-6xl w-full mx-auto">
          
          {currentStep === 0 && !isAnalyzing && (
            <div className="flex flex-col items-center justify-center min-h-[70vh] text-center max-w-2xl mx-auto">
              <span className="text-sm font-bold text-blue-400 tracking-wider uppercase mb-2">네이버 블로그 링크 하나로 영상을 바로 만듭니다.</span>
              <h2 className="text-3xl font-black text-white mb-8">リンク만 넣고 바로 시작</h2>
              <div className="w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl flex flex-col gap-5">
                <input
                  type="url"
                  className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-5 text-base text-slate-200 placeholder-slate-700 focus:outline-none focus:border-blue-500"
                  placeholder="네이버 블로그 링크를 붙여넣어 주세요"
                  value={blogUrl}
                  onChange={(e) => setBlogUrl(e.target.value)}
                />
                <button onClick={handleStartAnalysis} className="w-full bg-blue-600 hover:bg-blue-500 font-bold py-4 rounded-xl shadow-lg transition-all text-base">
                  다음 단계 분석 실행 ➔
                </button>
              </div>
            </div>
          )}

          {isAnalyzing && (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
              <div className="w-12 h-12 rounded-full border-4 border-blue-500/10 border-t-blue-500 animate-spin mb-4"></div>
              <p className="font-semibold text-slate-300">네이버 블로그 서버에서 실시간 고화질 이미지 에셋을 파싱 중입니다...</p>
            </div>
          )}

          {currentStep === 3 && (
            <div className="animate-fade-in">
              <span className="text-xs font-bold text-blue-400 uppercase tracking-wide">Step 3</span>
              <h3 className="text-2xl font-black text-white mt-1 mb-2">주요 이미지를 선택해주세요</h3>
              <p className="text-sm text-slate-400 mb-6">수집 및 추가된 이미지 중 체크 상태인 요소만 영상 트랙 소스로 반영됩니다. (선택됨: {selectedImages.length}개)</p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <label className="group relative aspect-video bg-slate-900/40 hover:bg-slate-900 border-2 border-dashed border-slate-800 hover:border-blue-500 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all gap-1.5 order-first shadow-inner">
                  <span className="text-2xl group-hover:scale-110 transition-transform">➕</span>
                  <span className="text-xs font-bold text-slate-500 group-hover:text-blue-400 transition-colors">이미지 직접 추가</span>
                  <input type="file" accept="image/*" multiple className="hidden" onChange={handleLocalImageUpload} />
                </label>

                {projectData.images.map((imgUrl, index) => {
                  const isChecked = selectedImages.includes(imgUrl);
                  return (
                    <div 
                      key={index} 
                      onClick={() => handleToggleImage(imgUrl)}
                      className={`group relative aspect-video bg-slate-900 rounded-xl overflow-hidden cursor-pointer shadow-lg border-2 transition-all duration-150 ${
                        isChecked ? 'border-blue-500 scale-[0.99]' : 'border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className={`absolute top-2 left-2 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold transition-all z-10 ${
                        isChecked ? 'bg-blue-600 text-white' : 'bg-black/50 border border-white/30 text-transparent'
                      }`}>
                        ✓
                      </div>
                      <img src={imgUrl} alt="asset" className={`w-full h-full object-cover transition-opacity duration-150 ${isChecked ? 'opacity-100' : 'opacity-40 group-hover:opacity-60'}`} referrerPolicy="no-referrer" />
                    </div>
                  );
                })}
              </div>
              <button onClick={() => setCurrentStep(6)} className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 font-bold rounded-xl text-sm transition-all shadow-md float-right">
                선택 이미지 확정 및 다음 단계 ➔
              </button>
            </div>
          )}

          {currentStep === 6 && (
            <div className="animate-fade-in">
              <span className="text-xs font-bold text-blue-400 uppercase tracking-wide">Step 6</span>
              <h3 className="text-2xl font-black text-white mt-1 mb-2">목소리를 선택해주세요</h3>
              <p className="text-sm text-slate-400 mb-6">나레이션 트랙에 매핑할 페르소나 음성 합성 레이어입니다.</p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                {[
                  { id: 'alloy', name: '20대 여자 (Alloy)', desc: '나긋나긋 명쾌한 쇼츠 여성 톤' },
                  { id: 'echo', name: 'ASMR 남자 (Echo)', desc: '잔잔하고 중후한 정보 전달 남성 톤' },
                  { id: 'onyx', name: '스포츠 MC (Onyx)', desc: '에너지 넘치고 활기찬 중계 톤' }
                ].map((voice) => (
                  <div
                    key={voice.id}
                    onClick={() => setProjectData(prev => ({ ...prev, selectedVoice: voice.id }))}
                    className={`p-5 rounded-2xl border cursor-pointer transition-all ${
                      projectData.selectedVoice === voice.id ? 'bg-blue-600/10 border-blue-500' : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-white text-base">{voice.name}</span>
                      <input type="radio" checked={projectData.selectedVoice === voice.id} readOnly />
                    </div>
                    <p className="text-xs text-slate-400">{voice.desc}</p>
                  </div>
                ))}
              </div>
              <button onClick={handleVoiceGeneration} className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 font-bold rounded-xl text-sm transition-all shadow-md float-right">
                🎙️ 목소리 인코딩 및 대본 합성 시작 ➔
              </button>
            </div>
          )}

          {currentStep === 7 && (
            <div className="animate-fade-in">
              <span className="text-xs font-bold text-blue-400 uppercase tracking-wide">Step 7</span>
              <h3 className="text-2xl font-black text-white mt-1 mb-2">영상 스타일을 선택해주세요</h3>
              <p className="text-sm text-slate-400 mb-6">렌더링될 자막 프리셋 스타일 바 디자인 사양입니다.</p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                {['전체 템플릿', '정보성 기본', '정보성 다크', '바이럴 민트'].map((tmpl, idx) => (
                  <div key={idx} className="aspect-[9/16] w-40 bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between shadow-md hover:border-slate-600 cursor-pointer">
                    <span className="text-xs font-bold text-slate-400">{tmpl}</span>
                    <div className="w-full h-24 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-center text-[10px] text-slate-700 font-mono">PREVIEW</div>
                  </div>
                ))}
              </div>
              <button onClick={handleFinalVideoGeneration} className="px-8 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl text-sm transition-all shadow-lg float-right">
                🎬 FFmpeg 최종 컴파일 엔진 구동 ➔
              </button>
            </div>
          )}

          {/* 💡 [슈퍼쇼츠 Step 8 완벽 이식] 자막 콘티 실시간 에디터 장착 */}
          {currentStep === 8 && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fade-in">
              <div className="lg:col-span-4 flex flex-col gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col items-center shadow-xl">
                  <span className="text-xs text-blue-400 font-bold mb-3 self-start uppercase tracking-wider">미리보기 영상</span>
                  <video src={projectData.videoUrl} controls className="w-56 aspect-[9/16] bg-black rounded-2xl shadow-2xl border border-slate-800" />
                </div>
              </div>

              <div className="lg:col-span-8 flex flex-col gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl">
                  <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
                    <h4 className="text-base font-black text-white flex items-center gap-2">
                      📋 실시간 장면 콘티 에디터 <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">{projectData.scenes.length}개 씬</span>
                    </h4>
                    <span className="text-xs text-slate-500">박스 내부의 글자를 직접 수정할 수 있습니다.</span>
                  </div>

                  <div className="flex flex-col gap-4 max-h-[550px] overflow-y-auto pr-2">
                    {projectData.scenes.map((scene) => (
                      <div key={scene.id} className="bg-slate-950 border border-slate-800/80 rounded-2xl p-5 flex flex-col gap-3 shadow-inner">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-mono bg-blue-600/10 text-blue-400 border border-blue-500/20 px-3 py-1 rounded-full font-bold">Scene 0{scene.id} ({scene.time})</span>
                          <span className="text-slate-500 font-mono text-[11px]">🎬 비디오 매핑: {scene.desc}</span>
                        </div>
                        
                        <div className="flex flex-col gap-1.5">
                          <span className="text-[10px] text-emerald-400 font-black tracking-wide uppercase">💬 화면 자막 및 음성 스크립트 편집</span>
                          <textarea
                            value={scene.script}
                            onChange={(e) => handleSceneTextChange(scene.id, 'script', e.target.value)}
                            className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-sm text-slate-200 focus:outline-none focus:border-blue-500 resize-none font-sans leading-relaxed transition-all"
                            rows={2}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

        </main>
      </div>

    </div>
  );
}

export default App;

// src/App.jsx (일부 핵심 기능 수정)
// ... 기존 코드 유지 ...
  
  // 💡 실제 AI 음성 합성 후 샘플 청취 (사운드 카드에 연결)
  const playVoiceSample = async (voiceId, e) => {
    e.stopPropagation();
    alert("AI가 샘플 목소리를 생성 중입니다. 잠시만 기다려주세요...");
    try {
      const response = await fetch('http://127.0.0.1:8000/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: "지금 선택하신 성우의 목소리입니다.", voice: voiceId })
      });
      const data = await response.json();
      const audio = new Audio(data.audio_url);
      audio.play();
    } catch(err) {
      alert("샘플 생성 실패");
    }
  };

  // 💡 영상 제작 시 로딩 상태 강화
  const handleFinalVideoGeneration = async () => {
    setStatusMessage('rendering_video');
    try {
      const response = await fetch('http://127.0.0.1:8000/api/video', { 
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ template: projectData.selectedTemplate })
      });
      const data = await response.json();
      setProjectData(prev => ({ ...prev, videoUrl: data.video_url }));
      setCurrentStep(5);
    } catch (error) {
      alert('영상 제작 중 오류 발생');
    } finally {
      setStatusMessage('');
    }
  };
// ... 나머지 코드는 그대로 유지 ...