import { create } from 'zustand';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const useProjectStore = create((set, get) => ({
  currentStep: 0,
  blogUrl: '',
  statusMode: '', 
  taskId: '', 
  selectedImages: [],
  
  fxSettings: { autoFx: true, autoBgm: true, bgmTrack: 'track_01', addIntro: false },
  customTemplate: { fontFamily: 'Pretendard', fontSize: 42, colorLine1: '#FFFFFF', colorLine2: '#FFD400', channelName: '내전용 숏츠', hasBgBox: true },

  projectData: {
    title: '', script: { hook: '', body: '', ending: '' }, images: [], scenes: [], selectedVoice: 'alloy', selectedTemplate: 'basic', audioUrl: '', videoUrl: ''
  },

  setCurrentStep: (step) => set({ currentStep: step }),
  setBlogUrl: (url) => set({ blogUrl: url }),
  setSelectedVoice: (voiceId) => set((state) => ({ projectData: { ...state.projectData, selectedVoice: voiceId } })),
  setSelectedTemplate: (templateId) => set((state) => ({ projectData: { ...state.projectData, selectedTemplate: templateId } })),
  toggleFxSetting: (field) => set((state) => ({ fxSettings: { ...state.fxSettings, [field]: !state.fxSettings[field] } })),
  setBgmTrack: (trackId) => set((state) => ({ fxSettings: { ...state.fxSettings, bgmTrack: trackId } })),
  updateCustomTemplate: (field, value) => set((state) => ({ customTemplate: { ...state.customTemplate, [field]: value } })),

  handleStartAnalysis: async () => {
    const { blogUrl } = get();
    if (!blogUrl) { alert('네이버 블로그 URL을 입력해주세요.'); return; }
    set({ statusMode: 'analyzing' });
    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: blogUrl }),
      });
      const data = await response.json();
      set((state) => ({
        taskId: data.task_id, 
        projectData: { ...state.projectData, title: data.title, images: data.images || [], script: data.script, scenes: data.scenes || [] },
        selectedImages: data.images || [],
        currentStep: 1 
      }));
    } catch { alert('분석 오류가 발생했습니다.'); }
    finally { set({ statusMode: '' }); }
  },

  handleScriptChange: (field, value) => {
    set((state) => ({ projectData: { ...state.projectData, script: { ...state.projectData.script, [field]: value } } }));
  },

  handleToggleImage: (imgUrl) => {
    set((state) => {
      const isChecked = state.selectedImages.includes(imgUrl);
      const updated = isChecked ? state.selectedImages.filter(url => url !== imgUrl) : [...state.selectedImages, imgUrl];
      return { selectedImages: updated };
    });
  },

  handleLocalImageUpload: (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    const newImageUrls = files.map(file => URL.createObjectURL(file));
    set((state) => ({
      projectData: { ...state.projectData, images: [...state.projectData.images, ...newImageUrls] },
      selectedImages: [...state.selectedImages, ...newImageUrls]
    }));
  },

  playVoiceSample: async (voiceId, e) => {
    e.stopPropagation();
    const { taskId } = get();
    alert("AI 성우가 원고 일부를 읽어줍니다. 잠시만 기다려주세요...");
    try {
      const response = await fetch(`${API_BASE_URL}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId, hook: "테스트", body: "테스트", ending: "완료", voice: voiceId })
      });
      const data = await response.json();
      if (data.audio_url) new Audio(data.audio_url).play();
    } catch { alert("샘플 듣기 실패"); }
  },

  handleVoiceGeneration: async () => {
    const { projectData, taskId } = get();
    set({ statusMode: 'processing_tts' });
    try {
      const response = await fetch(`${API_BASE_URL}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          task_id: taskId,
          hook: projectData.script.hook,
          body: projectData.script.body,
          ending: projectData.script.ending,
          voice: projectData.selectedVoice 
        })
      });
      const data = await response.json();
      set(() => ({ projectData: { ...projectData, audioUrl: data.audio_url }, currentStep: 4 }));
    } catch { alert('음성 생성에 실패했습니다.'); }
    finally { set({ statusMode: '' }); }
  },

  handleFinalVideoGeneration: async () => {
    const { projectData, selectedImages, fxSettings, customTemplate, taskId } = get();
    set({ statusMode: 'rendering_video' });
    try {
      const response = await fetch(`${API_BASE_URL}/api/video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          task_id: taskId,
          images: selectedImages,
          template: projectData.selectedTemplate,
          settings: { 
            ...fxSettings, ...customTemplate,
            hook_text: projectData.script.hook, body_text: projectData.script.body, ending_text: projectData.script.ending
          } 
        })
      });

      // 🚨 [진짜 에러 추적기] 무작정 json()으로 파싱하지 않고, 텍스트로 먼저 받습니다.
      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (err) {
        // 서버가 터져서 JSON 대신 빈 문자열이나 에러 코드를 보냈을 때 여기서 방어합니다.
        throw new Error(`서버 응답 파싱 실패 (JSON 아님).\n\n서버 상태: ${response.status}\n응답 내용:\n${text.substring(0, 200)}`);
      }

      if (!response.ok) {
        throw new Error(data.detail || JSON.stringify(data));
      }

      set((set_state) => ({ projectData: { ...set_state.projectData, videoUrl: data.video_url }, currentStep: 5 }));
    } catch (error) {
      console.error("🚨 비디오 생성 상세 에러:", error);
      // 🚨 [에러 경고창 출력] 숨겨졌던 진짜 에러가 드디어 화면에 뜹니다!
      alert(`[영상 제작 실패 진짜 원인]\n\n${error.message}\n\n👉 VS Code의 파이썬 백엔드 터미널 창을 꼭 확인하세요!`);
    } finally { 
      set({ statusMode: '' }); 
    }
  }
}));