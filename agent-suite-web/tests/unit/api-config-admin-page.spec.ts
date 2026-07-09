import ElementPlus from 'element-plus';
import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import ApiConfigAdminPage from '@views/admin/ApiConfigAdminPage.vue';
import type { AgentApiConfigView, AgentName } from '@/types/admin-api-config';

const apiMocks = vi.hoisted(() => ({
  buildDefaultAgentApiConfigs: vi.fn(),
  listAgentApiConfigs: vi.fn(),
  updateAgentApiConfig: vi.fn(),
}));

vi.mock('@api/admin-api-config', () => apiMocks);

vi.mock('@stores/auth', () => ({
  useAuthStore: () => ({
    profile: {
      public_id: 'user-1',
      role: 'admin',
    },
  }),
}));

vi.mock('@stores/toast', () => ({
  useToastStore: () => ({
    success: vi.fn(),
  }),
}));

function configRow(agent: AgentName, displayName: string): AgentApiConfigView {
  return {
    user_public_id: 'user-1',
    api_type: `${agent}_deepseek`,
    display_name: displayName,
    base_url: null,
    model: null,
    api_key_hint: null,
    timeout_seconds: null,
    max_retries: null,
    enabled: false,
    extra: null,
    updated_by: 'user-1',
    updated_at: '2026-07-05T00:00:00.000Z',
  };
}

describe('ApiConfigAdminPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const rowsByAgent: Record<AgentName, AgentApiConfigView[]> = {
      legal: [configRow('legal', 'Legal Only')],
      recruitment: [configRow('recruitment', 'Recruitment Only')],
      data: [configRow('data', 'Data Only')],
    };
    apiMocks.listAgentApiConfigs.mockImplementation(async (agent: AgentName) => rowsByAgent[agent]);
  });

  it('switches the visible config table when agent tabs are clicked', async () => {
    const wrapper = mount(ApiConfigAdminPage, {
      global: {
        plugins: [ElementPlus],
        stubs: {
          ApiConfigEditor: true,
        },
      },
    });
    await flushPromises();

    expect(wrapper.findAll('.api-config-page__tab-body')).toHaveLength(1);
    expect(wrapper.text()).toContain('Legal Only');
    expect(wrapper.text()).not.toContain('Recruitment Only');

    const tabs = wrapper.findAll('.api-config-page__agent-tab');
    await tabs[1].trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('Recruitment Only');
    expect(wrapper.text()).not.toContain('Legal Only');

    await tabs[2].trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('Data Only');
    expect(wrapper.text()).not.toContain('Recruitment Only');
  });
});
