#!/usr/bin/env ruby
# nx_shims_test.rb — 프리로드 심 사전 검증 (실제 루비에서 RGSS를 스텁으로 흉내).
# 사용법: ruby tests/nx_shims_test.rb <game 경로>
# 통과 못 하면 pack_psb.py가 빌드를 중단한다. 배포 전 마지막 관문.

raise "사용법: ruby tests/nx_shims_test.rb <game경로>" unless ARGV[0]
GAMEDIR = ARGV[0]
$failures = []

def assert(cond, msg)
  if cond
    puts "  ok  #{msg}"
  else
    puts "  FAIL #{msg}"
    $failures << msg
  end
end

#--- RGSS 스텁 ---------------------------------------------------------------
class Bitmap
  attr_reader :width, :height
  def initialize(a = 0, b = 0)
    if a.is_a?(String) then @width, @height = 512, 384      # 파일 로드 흉내
    else @width, @height = a, b
    end
  end
  def disposed?; false; end
end

class Rect
  attr_accessor :x, :y, :width, :height
  def initialize(x, y, w, h); @x, @y, @width, @height = x, y, w, h; end
end

class Viewport
  attr_accessor :rect, :z
  def initialize(x = 0, y = 0, w = 0, h = 0); @rect = Rect.new(x, y, w, h); end
  def disposed?; false; end
  def dispose; end
end

class Sprite
  attr_accessor :x, :y, :bitmap, :opacity
  def initialize(vp = nil); @x = 0; @y = 0; @opacity = 255; end
  def disposed?; false; end
  def dispose; end
end

class IconSprite < Sprite
  def setBitmap(p); end
end

module Graphics
  W, H = 683, 384
  class << self
    def width; W; end
    def height; H; end
    def update; end
  end
end

module Input
  A = 1; B = 2; C = 3; X = 4; Y = 5; Z = 6; L = 7; R = 8
  UP = 9; DOWN = 10; LEFT = 11; RIGHT = 12

  class << self
    attr_accessor :triggers, :text_input_state, :gets_calls
    def triggers; @triggers ||= {}; end
    def trigger?(k); triggers[k] ? true : false; end
    def triggerex?(k); false; end
    def text_input; @text_input_state ||= false; end
    def text_input=(v); (@text_input_history ||= []) << v; @text_input_state = v; end
    def text_input_history; @text_input_history ||= []; end
    def gets; (@gets_calls ||= 0); @gets_calls += 1; ""; end
    def gets_calls; @gets_calls ||= 0; end
    def update; end
  end
end

module NX
  def self.log(m); end
end

#--- 프리로드 심 로드 (엔진 의존 없는 두 개만: bezel, psb-fixes) ---------------
%w[nx-psb-fixes.rb].each do |f|
  path = File.join(GAMEDIR, "lib", f)
  load path
  puts "  ok  로드: lib/#{f}"
rescue ScriptError, StandardError => e
  puts "  FAIL 로드 불가 lib/#{f}: #{e.class}: #{e.message}"
  $failures << "load #{f}"
end

#--- 게임/플러그인 클래스 스텅 (스크립트 로드 이후 생긴 것을 시뮬레이션) ------
class Scene_Intro
  def cyclePics
    @sp = Sprite.new
    @sp.bitmap = Bitmap.new(512, 384)   # 스플래시 그림 부착
    @seen_x = @sp.x
  end
  attr_reader :seen_x
end

class PokemonLoad_Scene
  def pbStartScene(*a)
    @viewport = Viewport.new(0, 0, Graphics.width, Graphics.height)
  end
  def pbStartDeleteScene(*a)
    @viewport = Viewport.new(0, 0, Graphics.width, Graphics.height)
  end
  attr_reader :viewport
end

class PokemonSurvivorNameInputScene
  KEY_ENTER = 0x0D
  KEY_BACKSPACE = 0x08
  def initialize; @native_text_input = true; @done = false; @name = ""; end
  attr_accessor :native_text_input, :done, :name
  def key_trigger?(code)
    return true if @native_text_input && Input.triggerex?(:RETURN)   # 실기에선 안 옴
    false
  end
  def update_input; :orig; end
end

#--- 프레임 1회 실행: 훅 설치 --------------------------------------------------
Graphics.update

puts "== 이름 입력 =="
sc = PokemonSurvivorNameInputScene.new
assert(sc.key_trigger?(PokemonSurvivorNameInputScene::KEY_ENTER) == false, "버튼 없으면 ENTER 아님")
sc.name = "RED"
Input.triggers[Input::C] = true
assert(sc.key_trigger?(PokemonSurvivorNameInputScene::KEY_ENTER) == true, "이름 있을 때 남쪽(스위치 B)=ENTER")
Input.triggers.clear
Input.triggers[Input::B] = true
assert(sc.key_trigger?(PokemonSurvivorNameInputScene::KEY_ENTER) == true, "이름 있을 때 동쪽(스위치 A)=ENTER")
Input.triggers.clear
Input.triggers[Input::X] = true
assert(sc.key_trigger?(PokemonSurvivorNameInputScene::KEY_BACKSPACE) == true, "북쪽(스위치 X)=지우기")
Input.triggers.clear
Input.triggers[Input::A] = true
assert(sc.key_trigger?(PokemonSurvivorNameInputScene::KEY_BACKSPACE) == true, "서쪽(스위치 Y)=지우기")
Input.triggers.clear

puts "== 빈 이름에 A = 키보드 재호출 =="
sc2 = PokemonSurvivorNameInputScene.new
sc2.name = ""
h0 = Input.text_input_history.length
Input.triggers[Input::C] = true
r = sc2.key_trigger?(PokemonSurvivorNameInputScene::KEY_ENTER)
Input.triggers.clear
h = Input.text_input_history
assert(r == false, "빈 이름이면 ENTER가 아니라 재호출로 흡수")
assert(h[-2] == false && h[-1] == true, "text_input false→true (키보드 재등장)")

puts "== 키보드 재호출 (L/R) =="
sc2 = PokemonSurvivorNameInputScene.new
Input.triggers[Input::L] = true
r = sc2.update_input
Input.triggers.clear
hist = Input.text_input_history
assert(r == true, "L누르면 update_input 참 반환")
assert(hist[-2] == false && hist[-1] == true, "text_input false→true 토글 (swkbd 재호출)")
assert(Input.gets_calls >= 1, "재호출 전 버퍼 비움(Input.gets)")

puts "== 스플래시 중앙 정렬 =="
intro = Scene_Intro.new
intro.cyclePics
assert(intro.seen_x == 85, "512px 그림 x=85 (683 기준 중앙)")
sp2 = Sprite.new; sp2.bitmap = Bitmap.new(512, 384)
assert(sp2.y == 0, "높이 384는 y=0")
sp3 = Sprite.new; sp3.bitmap = Bitmap.new(683, 200)
assert(sp3.y == 0, "스플래시 컨텍스트 밖 그림은 중앙 정렬하지 않음")
assert(sp3.x == 0, "683폭 그림 x=0 그대로")

puts "== 로드 화면 중앙 이동 =="
ls = PokemonLoad_Scene.new
ls.pbStartScene
assert(ls.viewport.rect.x == 85 && ls.viewport.rect.width == 512, "뷰포트 (85,0,512,384)")
ls2 = PokemonLoad_Scene.new
ls2.pbStartDeleteScene
assert(ls2.viewport.rect.x == 85, "삭제화면도 중앙")

puts "== 멱등성 =="
Graphics.update; Graphics.update
sc3 = PokemonSurvivorNameInputScene.new
sc3.name = "RED"
Input.triggers[Input::C] = true
ok = sc3.key_trigger?(PokemonSurvivorNameInputScene::KEY_ENTER)
Input.triggers.clear
assert(ok == true, "여러 프레임 후에도 이중 래핑 없이 정상 동작")


#--- 결과 ---------------------------------------------------------------------
if $failures.empty?
  puts "\n모든 심 검증 통과 (#{Time.now.strftime('%F %T')})"
  exit 0
else
  puts "\n#{$failures.size}개 실패:"
  $failures.each { |f| puts "  - #{f}" }
  exit 1
end
