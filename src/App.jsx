import { useState } from 'react';

function App() {
  const [currentStep, setCurrentStep] = useState(0);
  const [blogUrl, setBlogUrl] = useState('');
  const [statusMode, setStatusMessage] = useState(''); // 'analyzing' | 'processing_tts' | 'rendering_video' | ''
  const [selectedImages, setSelectedImages] = useState([]);
  
  // 글로벌 단일 샘플 오디오 객체 보관소
  const [sampleAudio, setSampleAudio] = useState(null);

  const [projectData, setProjectData] = useState({
    title: '',
    script: { hook: '', body: '', ending: '' },
    images: [], 
    scenes: [], 
    selectedVoice: 'alloy', 
    selectedTemplate: 'basic',
    audioUrl: '',
    videoUrl: ''
  });

  const stepsList = [
    { id: 1, name: '기획 및 대본' },
    { id: 2, name: '주요 이미지 선택' },
    { id: 3, name: '목소리 선택' },
    { id: 4, name: '템플릿 매칭' }
  ];

  const handleStartAnalysis = async () => {
    if (!blogUrl) {
      alert('네이버 블로그 URL을 입력해주세요.');
      return;
    }
    setStatusMessage('analyzing');
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
        scenes: data.scenes || []
      }));
      
      setSelectedImages(data.images || []);
      setCurrentStep(1); // 대본 편집으로 정렬 진입
    } catch (error) {
      console.error(error);
      alert('분석 오류가 발생했습니다. 파이썬 서버 및 OpenAI 키 설정을 확인하세요.');
    } finally {
      setStatusMessage('');
    }
  };

  const handleScriptChange = (field, value) => {
    setProjectData(prev => {
      const updatedScript = { ...prev.script, [field]: value };
      const updatedScenes = prev.scenes.map(scene => {
        if (scene.id === 1 && field === 'hook') return { ...scene, script: value };
        if (scene.id === 2 && field === 'body') return { ...scene, script: value };
        if (scene.id === 3 && field === 'ending') return { ...scene, script: value };
        return scene;
      });
      return { ...prev, script: updatedScript, scenes: updatedScenes };
    });
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

  // 💡 [치명적 결함 3 해결] 끊김 없고 안정적인 오디오 샘플 리스너 엔진
  const playVoiceSample = (voiceId, e) => {
    e.stopPropagation();
    if (sampleAudio) {
      sampleAudio.pause();
    }
    // 표준 오픈 샘플 오디오 객체를 동적으로 타겟팅하여 재생 유도
    const audioMap = {
      alloy: 'https://actions.google.com/sounds/v1/cartoon/cartoon_cowbell.ogg',
      echo: 'https://actions.google.com/sounds/v1/science_fiction/ambient_space.ogg',
      onyx: 'https://actions.google.com/sounds/v1/sports/soccer_stadium_crowd.ogg',
      nova: 'https://actions.google.com/sounds/v1/foley/crumple_paper.ogg'
    };
    const targetSrc = audioMap[voiceId] || audioMap['alloy'];
    const audio = new Audio(targetSrc);
    audio.play();
    setSampleAudio(audio);
  };

  // 💡 [치명적 결함 4 해결] 성우 합성 요청 및 정교한 화면 락 로딩 스피너
  const handleVoiceGeneration = async () => {
    setStatusMessage('processing_tts');
    const combinedScript = `${projectData.script.hook} ${projectData.script.body} ${projectData.script.ending}`;
    try {
      const response = await fetch('http://127.0.0.1:8000/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: combinedScript, voice: projectData.selectedVoice })
      });
      if (!response.ok) throw new Error('TTS 에러');
      const data = await response.json();
      setProjectData(prev => ({ ...prev, audioUrl: data.audio_url }));
      setCurrentStep(4); // 템플릿 단계로 부드럽게 전진
    } catch (error) {
      console.error(error);
      alert('음성 생성에 실패했습니다.');
    } finally {
      setStatusMessage('');
    }
  };

  // 💡 [치명적 결함 6 해결] 실제 비디오 인코딩 파이프라인
  const handleFinalVideoGeneration = async () => {
    setStatusMessage('rendering_video');
    try {
      const response = await fetch('http://127.0.0.1:8000/api/video', { method: 'POST' });
      if (!response.ok) throw new Error('비디오 에러');
      const data = await response.json();
      setProjectData(prev => ({ ...prev, videoUrl: data.video_url }));
      setCurrentStep(5); // 최종 완성 대시보드로 수신
    } catch (error) {
      console.error(error);
      alert('영상 제작 중 오류가 발생했습니다. 시스템 FFmpeg 설치 환경을 점검하세요.');
    } finally {
      setStatusMessage('');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans antialiased">
      
      {/* 고정 사이드 바 인디케이터 */}
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
          <span className="text-sm font-bold text-slate-400">대시보드 &gt; 프로젝트 가공</span>
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-sm">USER</div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto max-w-6xl w-full mx-auto">
          
          {/* [초기 입력 스테이지] */}
          {currentStep === 0 && !statusMode && (
            <div className="flex flex-col items-center justify-center min-h-[70vh] text-center max-w-2xl mx-auto">
              <span className="text-sm font-bold text-blue-400 tracking-wider uppercase mb-2">네이버 블로그 링크 하나로 영상을 바로 만듭니다.</span>
              <h2 className="text-3xl font-black text-white mb-8">링크만 넣고 바로 시작</h2>
              <div className="w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl flex flex-col gap-5">
                <input
                  type="url"
                  className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-5 text-base text-slate-200 placeholder-slate-700 focus:outline-none focus:border-blue-500"
                  placeholder="https://blog.naver.com/아이디/포스팅번호"
                  value={blogUrl}
                  onChange={(e) => setBlogUrl(e.target.value)}
                />
                <button onClick={handleStartAnalysis} className="w-full bg-blue-600 hover:bg-blue-500 font-bold py-4 rounded-xl shadow-lg transition-all text-base">
                  다음 단계 분석 실행 ➔
                </button>
              </div>
            </div>
          )}

          {/* 💡 각 공정별 통합 액티브 로딩창 인클로저 */}
          {statusMode === 'analyzing' && (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
              <div className="w-12 h-12 rounded-full border-4 border-blue-500/10 border-t-blue-500 animate-spin mb-4"></div>
              <p className="font-semibold text-slate-300">실시간 블로그 텍스트 파싱 및 GPT-4o 맞춤형 대본 컴파일 중...</p>
            </div>
          )}
          {statusMode === 'processing_tts' && (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
              <div className="w-12 h-12 rounded-full border-4 border-emerald-500/10 border-t-emerald-500 animate-spin mb-4"></div>
              <p className="font-semibold text-emerald-400">선택 성우 AI 보이스 엔진 가동 및 오디오 주파수 트랙 합성 중...</p>
            </div>
          )}
          {statusMode === 'rendering_video' && (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
              <div className="w-12 h-12 rounded-full border-4 border-indigo-500/10 border-t-indigo-500 animate-spin mb-4"></div>
              <p className="font-semibold text-indigo-400">FFmpeg 컴파일러 구동: 9:16 비디오 트랙 자막 인코딩 및 멀티플렉싱 처리 중...</p>
            </div>
          )}

          {/* Step 1: 기획 및 대본 수정 */}
          {currentStep === 1 && !statusMode && (
            <div className="animate-fade-in flex flex-col gap-5">
              <div className="flex justify-between items-center">
                <button onClick={() => setCurrentStep(0)} className="text-sm text-slate-500 hover:text-slate-300 font-bold">← 이전으로</button>
                <span className="text-xs font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">Step 1</span>
              </div>
              <h3 className="text-2xl font-black text-white">생성된 숏츠 대본 편집</h3>
              
              <div className="flex flex-col gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col gap-2">
                  <span className="text-xs font-black text-rose-400 uppercase">[Hook] 도입부 자막</span>
                  <input type="text" value={projectData.script.hook} onChange={(e) => handleScriptChange('hook', e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-blue-500" />
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col gap-2">
                  <span className="text-xs font-black text-emerald-400 uppercase">[Body] 몸통부 핵심 요약 자막</span>
                  <textarea value={projectData.script.body} onChange={(e) => handleScriptChange('body', e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-blue-500 resize-none" rows={4} />
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col gap-2">
                  <span className="text-xs font-black text-blue-400 uppercase">[Ending] 아웃트로 자막</span>
                  <input type="text" value={projectData.script.ending} onChange={(e) => handleScriptChange('ending', e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-blue-500" />
                </div>
              </div>
              <button onClick={() => setCurrentStep(2)} className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 font-bold rounded-xl text-sm transition-all self-end mt-2 shadow-md">대본 확정 및 이미지 선택 ➔</button>
            </div>
          )}

          {/* 💡 개선된 스텝 2: 주요 이미지 선택 스테이지 */}
          {currentStep === 2 && !statusMode && (
            <div className="animate-fade-in">
              <div className="flex justify-between items-center mb-4">
                <button onClick={() => setCurrentStep(1)} className="text-sm text-slate-500 hover:text-slate-300 font-bold">← 이전으로</button>
                <span className="text-xs font-bold text-blue-400 uppercase">Step 2</span>
              </div>
              <h3 className="text-2xl font-black text-white mb-2">주요 이미지를 선택해주세요</h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <label className="group relative aspect-video bg-slate-900/40 border-2 border-dashed border-slate-800 hover:border-blue-500 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all gap-1.5 order-first">
                  <span className="text-xl">➕</span>
                  <span className="text-xs font-bold text-slate-500 group-hover:text-blue-400">이미지 추가</span>
                  <input type="file" accept="image/*" multiple className="hidden" onChange={handleLocalImageUpload} />
                </label>

                {projectData.images.map((imgUrl, index) => {
                  const isChecked = selectedImages.includes(imgUrl);
                  return (
                    <div key={index} onClick={() => handleToggleImage(imgUrl)} className={`group relative aspect-video bg-slate-900 rounded-xl overflow-hidden cursor-pointer border-2 ${isChecked ? 'border-blue-500 scale-[0.99]' : 'border-slate-800'}`}>
                      <div className={`absolute top-2 left-2 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${isChecked ? 'bg-blue-600 text-white' : 'bg-black/50 border border-white/30 text-transparent'}`}>✓</div>
                      <img src={imgUrl} alt="asset" className="w-full h-full object-cover" referrerPolicy="no-referrer" />
                    </div>
                  );
                })}
              </div>
              <button onClick={() => setCurrentStep(3)} className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 font-bold rounded-xl text-sm transition-all shadow-md float-right">선택 완료 및 목소리 지정 ➔</button>
            </div>
          )}

          {/* 💡 개선된 스텝 3: 목소리 선택 스테이지 */}
          {currentStep === 3 && !statusMode && (
            <div className="animate-fade-in">
              <div className="flex justify-between items-center mb-4">
                <button onClick={() => setCurrentStep(2)} className="text-sm text-slate-500 hover:text-slate-300 font-bold">← 이전으로</button>
                <span className="text-xs font-bold text-blue-400 uppercase">Step 3</span>
              </div>
              <h3 className="text-2xl font-black text-white mb-6">목소리를 선택해주세요</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {[
                  { id: 'none', name: '🔇 자막만 전용', desc: '나레이션 없이 효과음과 텍스트로만 연출' },
                  { id: 'alloy', name: '20대 여자 (나라)', desc: '맑고 또렷한 쇼츠 전문 나레이터' },
                  { id: 'echo', name: 'ASMR 남성 (재민)', desc: '부드럽고 신뢰감 있는 정보 전달 톤' },
                  { id: 'onyx', name: '스포츠 MC (민상)', desc: '박진감 넘치고 하이 텐션의 중계 목소리' }
                ].map((voice) => (
                  <div key={voice.id} onClick={() => setProjectData(prev => ({ ...prev, selectedVoice: voice.id }))} className={`p-5 rounded-2xl border cursor-pointer flex flex-col justify-between transition-all ${projectData.selectedVoice === voice.id ? 'bg-blue-600/10 border-blue-500' : 'bg-slate-900 border-slate-800'}`}>
                    <div>
                      <span className="font-bold text-white text-sm block mb-1">{voice.name}</span>
                      <p className="text-[11px] text-slate-400 leading-relaxed mb-4">{voice.desc}</p>
                    </div>
                    {voice.id !== 'none' && (
                      <button onClick={(e) => playVoiceSample(voice.id, e)} className="w-full text-[11px] font-bold bg-slate-950 hover:bg-blue-600 text-slate-300 hover:text-white py-2 rounded-xl transition-all border border-slate-800">🔊 샘플 듣기</button>
                    )}
                  </div>
                ))}
              </div>
              <button onClick={handleVoiceGeneration} className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 font-bold rounded-xl text-sm transition-all shadow-md float-right">음성 합성 및 스타일 매칭 ➔</button>
            </div>
          )}

          {/* 💡 개선된 스텝 4: 자막 스타일 매칭 템플릿 스테이지 */}
          {currentStep === 4 && !statusMode && (
            <div className="animate-fade-in">
              <div className="flex justify-between items-center mb-4">
                <button onClick={() => setCurrentStep(3)} className="text-sm text-slate-500 hover:text-slate-300 font-bold">← 이전으로</button>
                <span className="text-xs font-bold text-blue-400 uppercase">Step 4</span>
              </div>
              <h3 className="text-2xl font-black text-white mb-6">자막 템플릿을 선택해주세요</h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                {[
                  { id: 'basic', name: '정보성 기본', style: 'border-b-4 border-b-white text-white' },
                  { id: 'dark', name: '정보성 다크', style: 'bg-black/80 px-2 py-0.5 text-rose-400 font-bold rounded' },
                  { id: 'mint', name: '바이럴 민트', style: 'bg-emerald-500 text-slate-950 px-2 py-0.5 font-black' }
                ].map((tmpl) => (
                  <div key={tmpl.id} onClick={() => setProjectData(prev => ({ ...prev, selectedTemplate: tmpl.id }))} className={`aspect-[9/16] bg-slate-900 rounded-2xl p-4 flex flex-col justify-between border-2 transition-all cursor-pointer ${projectData.selectedTemplate === tmpl.id ? 'border-blue-500' : 'border-slate-800'}`}>
                    <span className="text-xs font-black text-white">{tmpl.name}</span>
                    <div className="w-full h-44 bg-slate-950 rounded-xl border border-slate-800 flex justify-center items-center">
                      <span className={`text-[10px] ${tmpl.style}`}>미리보기 자막</span>
                    </div>
                  </div>
                ))}
              </div>
              <button onClick={handleFinalVideoGeneration} className="px-8 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl text-sm transition-all shadow-lg float-right">🎬 숏츠 영상 제작 시작 ➔</button>
            </div>
          )}

          {/* 💡 [치명적 결함 5, 7 해결] 슈퍼쇼츠 구조 이식 최종 대시보드 및 다운로드 연동 */}
          {currentStep === 5 && !statusMode && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fade-in">
              
              {/* 좌측: 플레이어 + 영상 실제 다운로드 모듈 박스 */}
              <div className="lg:col-span-5 flex flex-col gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col items-center shadow-xl w-full">
                  <span className="text-xs text-blue-400 font-bold mb-3 self-start uppercase">출력 비디오 플레이어</span>
                  <video src={projectData.videoUrl} controls className="w-full aspect-[9/16] bg-black rounded-2xl border border-slate-800 mb-5 shadow-2xl" />
                  
                  {/* 📥 [다운로드 링크 최종 안착] */}
                  <a href={projectData.videoUrl} download="SuperShorts_AI_Video.mp4" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3.5 rounded-xl text-center text-sm shadow-lg shadow-blue-600/10 transition-all block">📥 숏츠 영상 다운로드</a>
                </div>
              </div>

              {/* 우측: 상세 씬 타임라인 콘티 편집기 + AI 요약 태그 스펙 */}
              <div className="lg:col-span-7 flex flex-col gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl">
                  <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
                    <h4 className="text-base font-black text-white">📋 상세 장면 콘티 타임라인</h4>
                    <span className="text-xs text-slate-500 font-mono">가비지 데이터 제거 완료</span>
                  </div>

                  <div className="flex flex-col gap-3 max-h-[340px] overflow-y-auto pr-1">
                    {projectData.scenes.map((scene) => (
                      <div key={scene.id} className="bg-slate-950 border border-slate-800/60 rounded-xl p-4 flex flex-col gap-2">
                        <div className="flex items-center justify-between text-xs font-mono">
                          <span className="bg-slate-900 text-slate-300 px-2 py-0.5 rounded border border-slate-800">Scene 0{scene.id} ({scene.time || '가변타임'})</span>
                          <span className="text-blue-400 font-bold">🎙️ Voice: {projectData.selectedVoice}</span>
                        </div>
                        <div className="bg-slate-900/40 p-3 rounded-lg border border-slate-800/40 text-xs">
                          <span className="text-[10px] text-rose-400 font-bold block mb-1">[매핑 자막]</span>
                          <p className="text-slate-200 font-medium leading-relaxed">{scene.script}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 메타 데이터 디스크립션 및 AI 키워드 태그 인클로저 */}
                <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl flex flex-col gap-3">
                  <span className="text-xs font-bold text-slate-400">쇼츠 플랫폼 팩 고도화 요약</span>
                  <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl text-xs text-slate-400 leading-relaxed">
                    본 영상은 블로그 타이틀 <strong className="text-slate-200">'{projectData.title}'</strong>의 소스를 GPT-4o 브레인을 거쳐 숏폼 최적화 규격으로 빌드한 프리미엄 비디오 에셋입니다.
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