import { create } from 'zustand';

// 🎯 [리뷰 결함 해결] 백엔드 주소가 사방에 박혀있던 하드코딩을 단 한 곳으로 통합 환경변수화
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const useProjectStore = create((set, get) => ({
  currentStep: 0,
  blogUrl: '',
  statusMode: '', 
  taskId: '', // 🎯 다중 동시 접속자 세션 격리를 위한 고유 키 저장소
  selectedImages: [],
  
  fxSettings: { autoFx: true, autoBgm: true, bgmTrack: 'track_01', addIntro: false },
  customTemplate: { fontFamily: 'Pretendard', fontSize: 42, colorLine1: '#FFFFFF', colorLine2: '#FFD400', channelName: '내 전용 숏츠', hasBgBox: true },

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
        taskId: data.task_id, // 서버가 발급한 유니크 세션 ID 수신
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
    alert("AI 성우가 맑고 선명한 음질의 샘플 보이스를 전송 중입니다...");
    try {
      const response = await fetch(`${API_BASE_URL}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId, hook: "샘플", body: "테스트", ending: "완료", voice: voiceId })
      });
      const data = await response.json();
      if (data.audio_url) new Audio(data.audio_url).play();
    } catch { alert("샘플 청취 실패"); }
  },

  handleVoiceGeneration: async () => {
    const { projectData, taskId } = get();
    set({ statusMode: 'processing_tts' });
    try {
      const response = await fetch(`${API_BASE_URL}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          task_id: taskId, // 세션 전달
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
          task_id: taskId, // 세션 전달
          images: selectedImages,
          template: projectData.selectedTemplate,
          settings: { 
            ...fxSettings, ...customTemplate,
            hook_text: projectData.script.hook, body_text: projectData.script.body, ending_text: projectData.script.ending
          } 
        })
      });
      const data = await response.json();
      set((set_state) => ({ projectData: { ...set_state.projectData, videoUrl: data.video_url }, currentStep: 5 }));
    } catch { alert('영상 합성 중 에러가 발생했습니다.'); }
    finally { set({ statusMode: '' }); }
  }
}));