# nx-psb-fixes.rb — PSB 스위치 변환용 런타임 패치 (프리로드 심).
#
# 왜 프리로드인가: 기기에서 Plugins 재컴파일이 조건 타이밍 탓에 안 돌아도
# 프리로드 심은 항상 실행된다. 플러그인 소스는 순정 그대로 두고 모든 조정은
# 여기서 게임/플러그인 클래스가 로드된 직후 한 번만 감아챈다.
#
#   1) 이름 입력: OSK(화상 키보드)는 글자만 주고 RETURN 스캔코드를 안 준다.
#      A/B = "다음 단계" — 이름이 비면 키보드 재호출, 차 있으면 확정(ENTER).
#      X/Y = 한 글자 지우기, L/R = 키보드 수동 재호출.
#   2) 스플래시 그림: 512px 아트가 x=0에 붙어 좌측으로 쏠림 → 중앙 정렬.
#   3) 로드 화면(이어하기/새게임): 512px 레이아웃을 뷰포트째 중앙 이동.
#
# 참고(스위치 물리버튼 → mkxp-z Input 상수, keybindings.cpp 기준):
#   A동쪽=Input::B, B남쪽=Input::C, X북쪽=Input::X, Y서쪽=Input::A, L/R=Input::L/R.
#   Input::START는 존재하지 않는다. 터치는 스크립트에 노출되지 않는다.

module NXPSBFix
  @fixes = {}

  class << self
    def log(msg)
      NX.log("[psbfix] #{msg}") if defined?(NX) && NX.respond_to?(:log)
    rescue
      nil
    end

    def done_once?(key)
      @fixes[key] ? true : false
    end

    def mark_done(key)
      @fixes[key] = true
    end
  end

  def self.splash_center?
    @splash_center ? true : false
  end

  #--- 감시: 매 프레임, 아직 못 박은 것만 ------------------------------------
  def self.revisar
    fix_name_input unless done_once?(:name)
    fix_splash unless done_once?(:splash)
    fix_load_screen unless done_once?(:load)
  end

  #--- 1) 이름 입력: 게임패드 → 키보드 매핑 -----------------------------------
  def self.fix_name_input
    return unless defined?(PokemonSurvivorNameInputScene)
    return unless PokemonSurvivorNameInputScene.method_defined?(:key_trigger?)
    mark_done(:name)
    PokemonSurvivorNameInputScene.class_eval do
      alias_method :nx_fix_key_trigger, :key_trigger?
      def key_trigger?(code)
        begin
          # 주의: class_eval 블록 안 def는 클래스 상수가 렉시컬로 안 풀린다 —
          # 반드시 const_get으로. (NameError가 무음 rescue에 묻히면 패치가 죽는다)
          key_enter = self.class.const_get(:KEY_ENTER)
          key_bs = self.class.const_get(:KEY_BACKSPACE)
          if code == key_enter && (Input.trigger?(Input::C) || Input.trigger?(Input::B))
            # A/B는 "다음 단계": 이름이 비어 있으면 확정해봤자 오류다 —
            # 대신 화상 키보드를 다시 띄워준다(실수로 닫혀도 복구).
            if @name.to_s.empty?
              Input.text_input = false
              Input.gets rescue nil
              Input.text_input = true
              return false
            end
            return true
          end
          if code == key_bs
            return true if Input.trigger?(Input::X)   # 스위치 X(북쪽)
            return true if Input.trigger?(Input::A)   # 스위치 Y(서쪽)
          end
        rescue
        end
        nx_fix_key_trigger(code)
      end

      alias_method :nx_fix_update_input, :update_input
      def update_input
        if @native_text_input && !@done
          begin
            if Input.trigger?(Input::L) || Input.trigger?(Input::R)
              Input.text_input = false
              Input.gets rescue nil       # 남은 버퍼 비우기
              Input.text_input = true     # 화상 키보드 다시 호출
              return true
            end
          rescue
          end
        end
        nx_fix_update_input
      end
    end
    log("nombre: A/B=ENTER(빈이름=teclado), X/Y=BORRAR, L/R=teclado")
  rescue Exception => e
    mark_done(:name)
    log("FALLO nombre #{e.class}: #{e.message}")
  end

  #--- 2) 스플래시 중앙 정렬 --------------------------------------------------
  def self.fix_splash
    return unless defined?(Scene_Intro) && Scene_Intro.method_defined?(:cyclePics)
    mark_done(:splash)
    Scene_Intro.class_eval do
      alias_method :nx_fix_cycle_pics, :cyclePics
      def cyclePics
        NXPSBFix.instance_variable_set(:@splash_center, true)
        begin
          nx_fix_cycle_pics
        ensure
          NXPSBFix.instance_variable_set(:@splash_center, false)
        end
      end
    end
    log("splash: centrado")
  rescue Exception => e
    mark_done(:splash)
    log("FALLO splash #{e.class}: #{e.message}")
  end

  #--- 3) 로드 화면 중앙 이동 --------------------------------------------------
  def self.fix_load_screen
    return unless defined?(PokemonLoad_Scene) && PokemonLoad_Scene.method_defined?(:pbStartScene)
    mark_done(:load)
    PokemonLoad_Scene.class_eval do
      alias_method :nx_fix_pbStartScene, :pbStartScene
      def pbStartScene(*args)
        nx_fix_pbStartScene(*args)
        off = (Graphics.width - 512) / 2
        @viewport.rect = Rect.new(off, 0, 512, Graphics.height) if off > 0 && @viewport
      end
      if method_defined?(:pbStartDeleteScene)
        alias_method :nx_fix_pbStartDeleteScene, :pbStartDeleteScene
        def pbStartDeleteScene(*args)
          nx_fix_pbStartDeleteScene(*args)
          off = (Graphics.width - 512) / 2
          @viewport.rect = Rect.new(off, 0, 512, Graphics.height) if off > 0 && @viewport
        end
      end
    end
    log("load screen: centrado")
  rescue Exception => e
    mark_done(:load)
    log("FALLO load screen #{e.class}: #{e.message}")
  end
end

# 스플래시 비트맵이 붙는 순간 좌표를 가운데로 (cyclePics 실행 중에만 활성화)
class Sprite
  alias_method :nx_fix_bitmap_set, :bitmap=
  def bitmap=(bmp)
    nx_fix_bitmap_set(bmp)
    if NXPSBFix.splash_center? && bmp && !bmp.disposed?
      begin
        self.x = (Graphics.width - bmp.width) / 2
        self.y = (Graphics.height - bmp.height) / 2
      rescue
      end
    end
  end
end

module Graphics
  class << self
    alias_method :nx_update_sin_psbfix, :update

    def update
      NXPSBFix.revisar
      nx_update_sin_psbfix
    end
  end
end
