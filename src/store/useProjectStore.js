import { create } from 'zustand';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// 🎨 영상 스타일 템플릿 (백엔드 video_service의 template 키와 1:1 매칭)
//  preview: 카드 안에서 폰 목업 미리보기를 그릴 때 쓰는 스타일 값
export const TEMPLATES = [
  {
    id: 'basic', name: '정보성', badge: '추천', desc: '깔끔하게 정보를 전달하는 클래식 스타일',
    preview: { bg: '#0f172a', title: '#ffffff', point: '#38bdf8', barBg: 'rgba(0,0,0,0.55)' },
  },
  {
    id: 'dark', name: '정보성 다크', badge: '', desc: '진한 배경으로 몰입감을 높인 스타일',
    preview: { bg: '#020617', title: '#ffffff', point: '#3b82f6', barBg: 'rgba(0,0,0,0.7)' },
  },
  {
    id: 'mint', name: '바이럴 민트', badge: '유행', desc: '민트 훅 제목과 검정 자막바 연출',
    preview: { bg: '#0b3d33', title: '#ffffff', point: '#34d399', barBg: 'rgba(0,0,0,0.8)' },
  },
  {
    id: 'sunset', name: '선셋', badge: 'NEW', desc: '따뜻한 앰버 포인트로 감성을 더한 스타일',
    preview: { bg: '#1f1300', title: '#ffffff', point: '#f59e0b', barBg: 'rgba(0,0,0,0.55)' },
  },
  {
    id: 'ocean', name: '오션', badge: 'NEW', desc: '시원한 블루 톤의 정보 전달 스타일',
    preview: { bg: '#0c1e3a', title: '#ffffff', point: '#22d3ee', barBg: 'rgba(2,18,40,0.7)' },
  },
];

const INITIAL_PROJECT = {
  title: '', script: { hook: '', body: '', ending: '' }, images: [], scenes: [],
  selectedVoice: 'alloy', selectedTemplate: 'basic', audioUrl: '', videoUrl: ''
};

export const useProjectStore = create((set, get) => ({
  currentStep: 0,
  blogUrl: '',
  statusMode: '',
  taskId: '',
  selectedImages: [],

  fxSettings: { autoFx: true, autoBgm: true, bgmTrack: 'track_01', addIntro: false, upscale: true },
  customTemplate: { fontFamily: 'Pretendard', fontSize: 42, colorLine1: '#FFFFFF', colorLine2: '#FFD400', channelName: '내전용 숏츠', hasBgBox: true },

  projectData: { ...INITIAL_PROJECT },

  setCurrentStep: (step) => set({ currentStep: step }),
  setBlogUrl: (url) => set({ blogUrl: url }),
  setSelectedVoice: (voiceId) => set((state) => ({ projectData: { ...state.projectData, selectedVoice: voiceId } })),
  setSelectedTemplate: (templateId) => set((state) => ({ projectData: { ...state.projectData, selectedTemplate: templateId } })),
  toggleFxSetting: (field) => set((state) => ({ fxSettings: { ...state.fxSettings, [field]: !state.fxSettings[field] } })),
  setBgmTrack: (trackId) => set((state) => ({ fxSettings: { ...state.fxSettings, bgmTrack: trackId } })),
  updateCustomTemplate: (field, value) => set((state) => ({ customTemplate: { ...state.customTemplate, [field]: value } })),

  // 처음 화면으로 돌아가 새 프로젝트 시작
  resetProject: () => set({
    currentStep: 0, blogUrl: '', statusMode: '', taskId: '', selectedImages: [],
    projectData: { ...INITIAL_PROJECT },
  }),

  handleStartAnalysis: async () => {
    const { blogUrl } = get();
    if (!blogUrl) { alert('네이버 블로그 주소를 입력해 주세요.'); return; }
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
    } catch { alert('블로그를 분석하지 못했어요. 주소를 다시 확인해 주세요.'); }
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

  // 선택한 이미지의 노출 순서를 변경 (영상에 이 순서대로 들어감)
  moveSelected: (index, dir) => set((state) => {
    const arr = [...state.selectedImages];
    const ni = index + dir;
    if (ni < 0 || ni >= arr.length) return {};
    [arr[index], arr[ni]] = [arr[ni], arr[index]];
    return { selectedImages: arr };
  }),

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
    try {
      const response = await fetch(`${API_BASE_URL}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId, hook: "샘플 음성입니다", body: "이런 목소리로 영상을 만들어요", ending: "완료", voice: voiceId })
      });
      const data = await response.json();
      if (data.audio_url && data.audio_url !== 'none') new Audio(data.audio_url).play();
    } catch { alert("샘플을 재생하지 못했어요."); }
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
    } catch { alert('음성을 만들지 못했어요.'); }
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

      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error(`서버 응답을 읽지 못했어요.\n\n상태 코드: ${response.status}\n응답: ${text.substring(0, 200)}`);
      }
      if (!response.ok) throw new Error(data.detail || JSON.stringify(data));

      set((s) => ({ projectData: { ...s.projectData, videoUrl: data.video_url }, currentStep: 5 }));
    } catch (error) {
      console.error("비디오 생성 에러:", error);
      alert(`영상을 만들지 못했어요.\n\n원인: ${error.message}\n\n백엔드 터미널의 오류 로그를 확인해 주세요.`);
    } finally {
      set({ statusMode: '' });
    }
  }
}));
