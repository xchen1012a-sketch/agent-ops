<script setup lang="ts">
import { computed } from 'vue';

export type AppIconName =
  | 'ArrowDown'
  | 'Box'
  | 'ChatDotRound'
  | 'CircleCheck'
  | 'CircleClose'
  | 'Close'
  | 'Collection'
  | 'Copy'
  | 'DataAnalysis'
  | 'Document'
  | 'DocumentChecked'
  | 'DocumentRemove'
  | 'Expand'
  | 'Files'
  | 'Folder'
  | 'Fold'
  | 'Histogram'
  | 'InfoFilled'
  | 'List'
  | 'Menu'
  | 'Monitor'
  | 'Moon'
  | 'Notebook'
  | 'Plus'
  | 'Play'
  | 'Refresh'
  | 'Search'
  | 'Setting'
  | 'Sunny'
  | 'TrendCharts'
  | 'ThumbsDown'
  | 'ThumbsUp'
  | 'User'
  | 'UserFilled'
  | 'View'
  | 'Warning';

const props = withDefaults(
  defineProps<{
    name: AppIconName | string;
    label?: string;
  }>(),
  {
    label: undefined,
  },
);

const normalizedName = computed(() => (iconPaths[props.name] ? props.name : 'Document'));

const iconPaths: Record<string, string[]> = {
  ArrowDown: ['M6 9l6 6 6-6'],
  Box: [
    'M21 16V8a2 2 0 0 0-1-1.73L13 2.27a2 2 0 0 0-2 0L4 6.27A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z',
    'M3.3 7 12 12l8.7-5',
    'M12 22V12',
  ],
  ChatDotRound: [
    'M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z',
    'M8.5 12h.01',
    'M12 12h.01',
    'M15.5 12h.01',
  ],
  CircleCheck: ['M22 11.08V12a10 10 0 1 1-5.93-9.14', 'M22 4 12 14.01l-3-3'],
  CircleClose: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z', 'M15 9l-6 6', 'M9 9l6 6'],
  Close: ['M18 6 6 18', 'M6 6l12 12'],
  Collection: ['M5 4h14v16H5z', 'M9 8h6', 'M9 12h6', 'M9 16h4'],
  Copy: [
    'M8 8h11a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z',
    'M4 16H3a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h11a1 1 0 0 1 1 1v1',
  ],
  DataAnalysis: ['M4 19V5', 'M4 19h16', 'M8 16v-5', 'M12 16V8', 'M16 16v-8', 'M20 16v-3'],
  Document: [
    'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z',
    'M14 2v6h6',
    'M8 13h8',
    'M8 17h6',
  ],
  Expand: ['M9 18l6-6-6-6'],
  Files: [
    'M14 2H6a2 2 0 0 0-2 2v14',
    'M8 6h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z',
  ],
  Folder: ['M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'],
  Fold: ['M15 18l-6-6 6-6'],
  Histogram: ['M4 19V5', 'M4 19h16', 'M8 16V9', 'M12 16V5', 'M16 16v-4'],
  InfoFilled: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z', 'M12 10v6', 'M12 7h.01'],
  List: ['M8 6h13', 'M8 12h13', 'M8 18h13', 'M3 6h.01', 'M3 12h.01', 'M3 18h.01'],
  Menu: ['M4 6h16', 'M4 12h16', 'M4 18h16'],
  Monitor: ['M4 5h16v12H4z', 'M8 21h8', 'M12 17v4'],
  Moon: ['M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z'],
  Notebook: [
    'M6 3h12a2 2 0 0 1 2 2v16H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z',
    'M8 7h8',
    'M8 11h8',
    'M8 15h5',
  ],
  Plus: ['M12 5v14', 'M5 12h14'],
  Play: ['M8 5v14l11-7z'],
  Refresh: ['M21 12a9 9 0 0 1-15.5 6.3', 'M3 12A9 9 0 0 1 18.5 5.7', 'M18 2v4h-4', 'M6 22v-4h4'],
  Search: ['M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16z', 'M21 21l-4.35-4.35'],
  Setting: [
    'M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5z',
    'M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.65 1.65 0 0 0 15 19.4a1.65 1.65 0 0 0-1 .6 1.65 1.65 0 0 0-.4 1.1V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 8 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-.6-1 1.65 1.65 0 0 0-1.1-.4H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 8a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-.6 1.65 1.65 0 0 0 .4-1.1V3a2 2 0 1 1 4 0v.09A1.65 1.65 0 0 0 16 4.6a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.6.22 1 .79 1.1 1.4H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51.6z',
  ],
  Sunny: [
    'M12 4V2',
    'M12 22v-2',
    'M4.93 4.93 3.52 3.52',
    'M20.48 20.48l-1.41-1.41',
    'M2 12h2',
    'M20 12h2',
    'M4.93 19.07l-1.41 1.41',
    'M20.48 3.52l-1.41 1.41',
    'M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10z',
  ],
  TrendCharts: ['M3 17l6-6 4 4 7-9', 'M14 6h6v6'],
  ThumbsDown: [
    'M10 14H5.5a2 2 0 0 1-1.9-2.63l2-6A2 2 0 0 1 7.5 4H10v10z',
    'M10 14l3 6a2 2 0 0 0 2-2v-4h3.5a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2H10',
  ],
  ThumbsUp: [
    'M10 10h-4.5a2 2 0 0 0-1.9 2.63l2 6A2 2 0 0 0 7.5 20H10V10z',
    'M10 10l3-6a2 2 0 0 1 2 2v4h3.5a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H10',
  ],
  User: ['M20 21a8 8 0 0 0-16 0', 'M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z'],
  UserFilled: ['M20 21a8 8 0 0 0-16 0', 'M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z'],
  View: ['M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z'],
  Warning: [
    'M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z',
    'M12 9v4',
    'M12 17h.01',
  ],
};
</script>

<template>
  <svg
    class="app-icon"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="path in iconPaths[normalizedName]" :key="path" :d="path" />
  </svg>
  <span v-if="label" class="sr-only">{{ label }}</span>
</template>

<style scoped>
.app-icon {
  width: 1em;
  height: 1em;
  color: currentColor;
}
</style>
