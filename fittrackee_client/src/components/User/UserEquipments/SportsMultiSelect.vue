<template>
  <Multiselect
    v-if="sports"
    placeholder=""
    :id="name"
    :name="name"
    :disabled="disabled"
    v-model="selectedSports"
    :multiple="true"
    :options="sports"
    :taggable="true"
    label="translatedLabel"
    track-by="id"
    :selectLabel="$t('workouts.MULTISELECT.selectLabel')"
    :selectedLabel="$t('workouts.MULTISELECT.selectedLabel')"
    :deselectLabel="$t('workouts.MULTISELECT.deselectLabel')"
    @update:model-value="updateSelectedSports"
  />
</template>

<script setup lang="ts">
  import { onBeforeMount, ref, toRefs, watch } from 'vue'
  import type { Ref } from 'vue'
  import Multiselect from 'vue-multiselect'

  import type { ITranslatedSport } from '@/types/sports'

  interface Props {
    sports: ITranslatedSport[]
    name: string
    equipmentSports?: ITranslatedSport[]
    disabled?: boolean
  }
  const props = withDefaults(defineProps<Props>(), {
    equipmentSports: () => [],
    disabled: false,
  })
  const { equipmentSports, name, sports } = toRefs(props)

  const emit = defineEmits(['updatedValues'])

  const selectedSports: Ref<ITranslatedSport[]> = ref([])

  function updateSelectedSports(sportsList: ITranslatedSport[]) {
    emit(
      'updatedValues',
      sportsList.map((e) => e.id)
    )
  }

  watch(
    () => equipmentSports.value,
    async (newEquipmentSports: ITranslatedSport[]) => {
      selectedSports.value = newEquipmentSports
      updateSelectedSports(newEquipmentSports)
    }
  )

  onBeforeMount(() => {
    if (equipmentSports.value) {
      selectedSports.value = equipmentSports.value
    }
  })
</script>

<style scoped lang="scss">
  @use '~@/scss/vars.scss' as *;
  ::v-deep(.multiselect__input) {
    background-color: var(--input-bg-color);
  }
  ::v-deep(.multiselect__tags) {
    border: 1px solid var(--input-border-color);
    border-radius: $border-radius;
    background: var(--multiselect-tags-bg-color);
  }
  ::v-deep(.multiselect__input) {
    border-color: black;
  }
  ::v-deep(.multiselect__tag) {
    background-color: var(--multiselect-tag-bg-color);
    color: var(--multiselect-tag-color);
  }
  ::v-deep(.multiselect__tag-icon::after) {
    color: var(--multiselect-tag-color);
  }
  ::v-deep(.multiselect__tag-icon:focus),
  ::v-deep(.multiselect__tag-icon:hover) {
    background: var(--multiselect-tag-icon-hover-bg-color);
  }
  ::v-deep(.multiselect__tag-icon:focus::after),
  ::v-deep(.multiselect__tag-icon:hover::after) {
    color: var(--multiselect-tag-icon-hover-color);
  }

  ::v-deep(.multiselect__option) {
    background: var(--multiselect-option-bg-color);
    color: var(--multiselect-option-color);
  }

  ::v-deep(.multiselect__option--highlight),
  ::v-deep(.multiselect__option--highlight::after) {
    background: var(--multiselect-option-highlight-bg-color);
    color: var(--multiselect-option-highlight-color);
  }

  ::v-deep(.multiselect__option--selected.multiselect__option--highlight) {
    background: var(--multiselect-option-selected-highlight-bg-color);
    color: var(--multiselect-option-selected-highlight-color);
  }
  ::v-deep(
    .multiselect__option--selected.multiselect__option--highlight::after
  ) {
    background: var(--multiselect-option-selected-highlight-after-bg-color);
    color: var(--multiselect-option-selected-highlight-after-color);
  }

  ::v-deep(.multiselect__option--selected) {
    background-color: var(--multiselect-option-selected-bg-color);
    color: var(--multiselect-option-selected-color);
  }

  ::v-deep(.multiselect__content-wrapper) {
    border-color: var(--multiselect-content-wrapper-border-color);
  }

  .multiselect--disabled {
    background-color: var(--multiselect-disabled-bg-color);
    ::v-deep(.multiselect__select) {
      background: var(--multiselect-select-disabled-bg-color);
      color: var(--multiselect-select-disabled-color);
    }
  }
</style>
