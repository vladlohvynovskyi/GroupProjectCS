import pygame
import os
import random

class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self.current_music = None
        self.music_position = 0.0
        self.music_volume = 0.2
        self.sfx_volume = 0.2
        self._load_sounds()

        #Sanity
        self.sanity_channel = pygame.mixer.Channel(5)
        self.ghost_channel = pygame.mixer.Channel(6)
        self.sanity_combat_channel = pygame.mixer.Channel(7)
        self.sanity_whisper = pygame.mixer.Sound(
            os.path.join("assets", "sounds", "Crying_moaning_ambience_3.wav")
        )

        self.ghost_chior = pygame.mixer.Sound(
            os.path.join("assets", "sounds", "Ghost chior.wav")
        )

        self.sanity_combat = pygame.mixer.Sound(
            os.path.join("assets", "sounds", "Monster_grunt_long.wav")
        )

        self.sanity_whisper.set_volume(0.8)
        self.ghost_chior.set_volume(0.7)

        self.sanity_combat.set_volume(0.8)
    
    def _load_sounds(self):
        """Load sound effects"""
        # Load multiple sword sounds
        try:
            self.sword_sounds = []
            for i in range(1, 3):  # sword1.wav and sword2.wav
                sword = pygame.mixer.Sound(f"assets/sounds/slash{i}.wav")
                sword.set_volume(self.sfx_volume)
                self.sword_sounds.append(sword)
        except Exception as e:
            print(f"Could not load sword sounds: {e}")
            self.sword_sounds = []

        try:
            self.hurt_sounds = []
            for i in range(2, 5):  # hurt2.wav, hurt3.wav, hurt4.wav
                hurt = pygame.mixer.Sound(f"assets/sounds/hurt{i}.wav")
                hurt.set_volume(self.sfx_volume)
                self.hurt_sounds.append(hurt)
        except Exception as e:
            print(f"Could not load hurt sounds: {e}")
            self.hurt_sounds = []

        try:
            self.sounds["open_chest"] = pygame.mixer.Sound("assets/sounds/open_chest.wav")
            self.sounds["open_chest"].set_volume(self.sfx_volume)
        except Exception as e:
            print(f"Could not load open_chest.wav: {e}")

        try:
            self.sounds["campfire"] = pygame.mixer.Sound("assets/music/fireplace.wav")
            self.sounds["campfire"].set_volume(self.sfx_volume)
        except Exception as e:
            print(f"Could not load fireplace.wav from music folder: {e}")
        
        # Other sounds
        sound_files = {
            "death": "death.wav",
            "level_up": "level_up.wav",
            "slime_death": "slime_death.flac",
            "flying_monstrosity_death": "piggrunt2.wav",
            "bee_scared_death": "grunt1.wav",
            "battering_bat_death": "deathd.wav",
            "armored_golem_death": "deathb.wav"
            # Add more as needed
        }
        
        for name, filename in sound_files.items():
            try:
                sound = pygame.mixer.Sound(f"assets/sounds/{filename}")
                sound.set_volume(self.sfx_volume)
                self.sounds[name] = sound
            except Exception as e:
                print(f"Could not load sound: {filename} - {e}")
    
    def play_exploration_music(self):

        
        """Start or resume exploration background music from where it left off"""
        self.sanity_combat_channel.stop()
        
        try:
            if self.current_music == "combat":
                # Coming back from combat, resume from stored position
                pygame.mixer.music.load("assets/music/exploring.mp3")
                pygame.mixer.music.play(-1, start=self.music_position)
            elif self.current_music != "exploring":
                # First time playing
                pygame.mixer.music.load("assets/music/exploring.mp3")
                pygame.mixer.music.play(-1)
                self.music_position = 0.0
            elif not pygame.mixer.music.get_busy():
                # Was paused, just unpause
                pygame.mixer.music.unpause()
            
            pygame.mixer.music.set_volume(self.music_volume)
            self.current_music = "exploring"
        except Exception as e:
            print(f"Could not load exploration music: {e}")
    
    def play_combat_music(self, sanity=None):
        """Switch to combat music and save exploration position"""
        try:
            # Save current exploration music position before switching
            if self.current_music == "exploring" and pygame.mixer.music.get_busy():
                self.music_position = pygame.mixer.music.get_pos() / 1000.0  # Convert ms to seconds
            
            if sanity is not None and sanity < 35:
                pygame.mixer.music.stop()
                if not self.sanity_combat_channel.get_busy():
                    self.sanity_combat_channel.play(self.sanity_combat, loops=-1)
                self.sanity_combat_channel.set_volume(0.8)
                self.current_music = "sanity_combat"
            else:
                self.sanity_combat_channel.stop()
                pygame.mixer.music.load("assets/music/fight.wav")
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(self.music_volume)
                self.current_music = "combat"

            # pygame.mixer.music.load("assets/music/fight.wav")
            # pygame.mixer.music.play(-1)
            # pygame.mixer.music.set_volume(self.music_volume)
            # self.current_music = "combat"
        except Exception as e:
            print(f"Could not load combat music: {e}")

    def play_sword_sound(self):
        """Play a random sword slash sound"""
        if self.sword_sounds:
            random.choice(self.sword_sounds).play()
    
    def play_transition_sound(self):
        """Play enter fight transition sound"""
        if "enter_fight" in self.sounds:
            self.sounds["enter_fight"].play()
    
    def stop_music(self):
        """Stop background music"""
        pygame.mixer.music.stop()
        self.current_music = None
    
    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
    
    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)
        for sound in self.sword_sounds:
            sound.set_volume(self.sfx_volume)
        for sound in self.hurt_sounds:
            sound.set_volume(self.sfx_volume)

    def play_hurt_sound(self):
      """Play a random hurt sound"""
      if self.hurt_sounds:
          random.choice(self.hurt_sounds).play()

    def play_chest_sound(self):
      """Play chest opening sound"""
      if "open_chest" in self.sounds:
          self.sounds["open_chest"].play()

    def play_level_up_sound(self):
      """Play level up sound"""
      if "level_up" in self.sounds:
          self.sounds["level_up"].play()

    def play_death_sound(self):
      """Play death sound"""
      if "death" in self.sounds:
          self.sounds["death"].play()

    def play_campfire_sound(self):
        """Play campfire sound (looping) and lower exploration music"""
        if "campfire" in self.sounds:
            self.sounds["campfire"].play(-1)
            # Lower exploration music volume when near campfire
            pygame.mixer.music.set_volume(self.music_volume * 0.2)  # 20% volume

    def stop_campfire_sound(self):
        """Stop campfire sound and restore exploration music"""
        if "campfire" in self.sounds:
            self.sounds["campfire"].stop()
            # Restore exploration music volume
            pygame.mixer.music.set_volume(self.music_volume)  # Back to normal

    def play_enemy_death_sound(self, enemy_name):
      """Play specific death sound based on enemy name"""
      if enemy_name == "Spikey Slime" and "slime_death" in self.sounds:
          self.sounds["slime_death"].play()
      elif enemy_name == "Flying Monstrosity" and "flying_monstrosity_death" in self.sounds:
          self.sounds["flying_monstrosity_death"].play()
      elif enemy_name == "Bee Scared" and "bee_scared_death" in self.sounds:
          self.sounds["bee_scared_death"].play()
      elif enemy_name == "Battering Bat" and "battering_bat_death" in self.sounds:
          self.sounds["battering_bat_death"].play()
      elif enemy_name == "Armored Golem" and "armored_golem_death" in self.sounds:
          self.sounds["armored_golem_death"].play()
      elif "death" in self.sounds:
          self.sounds["death"].play()  # Default death sound

    def update_sanity_audio(self, sanity):
        if sanity <= 20:
            music_volume = 0.0
        elif sanity <= 30:
            music_volume = self.music_volume * 0.1
        elif sanity <= 40:
            music_volume = self.music_volume * 0.5
        else:


            music_volume = self.music_volume
        pygame.mixer.music.set_volume(music_volume)

        if sanity <= 35:
            if not self.sanity_channel.get_busy():
                self.sanity_channel.play(self.sanity_whisper, loops=-1)
            self.sanity_channel.set_volume(0.8)
        else:
            self.sanity_channel.stop()
        if sanity <= 20:
            if not self.ghost_channel.get_busy():
                self.ghost_channel.play(self.ghost_chior, loops=-1)
         
            self.ghost_channel.set_volume(0.7)
        else:
            self.ghost_channel.stop()